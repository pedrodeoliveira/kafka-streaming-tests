package main

import (
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"io/ioutil"
	"net/http"
	"os"
	"os/signal"
	"syscall"
	"time"

	"github.com/lovoo/goka"
)

var (
	brokers                 = []string{"localhost:9092"}
	inputTopic  goka.Stream = "input-topic"
	group       goka.Group  = "streaming-goka"
	outputTopic goka.Stream = "output-topic"

	predictionURL string = "http://localhost:8000/predictions"
)

// The inputData is the object that is received in the input stream.
type inputData struct {
	UID  string `json:"uid"`
	Text string `json:"text"`
}

// The outputData is the object that is publised to the output stream.
type outputData struct {
	UID                       string  `json:"uid"`
	Text                      string  `json:"text"`
	Category                  string  `json:"category"`
	Subcategory               string  `json:"subcategory"`
	Confidence                float32 `json:"confidence"`
	Model                     string  `json:"model"`
	Version                   int     `json:"version"`
	PublishTimestamp          int64   `json:"publish_ts"`
	StreamingConsumeTimestamp int64   `json:"streaming_consume_ts"`
}

// This codec allows marshalling (encode) and unmarshalling (decode) the inputData to and from the
// group table.
type inputDataCodec struct{}

// Encodes a inputData into []byte
func (jc *inputDataCodec) Encode(value interface{}) ([]byte, error) {
	if _, isInputData := value.(*inputData); !isInputData {
		return nil, fmt.Errorf("codec requires value *inputData, got %T", value)
	}
	return json.Marshal(value)
}

// Decodes a inputData from []byte to it's go representation.
func (jc *inputDataCodec) Decode(data []byte) (interface{}, error) {
	var (
		c   inputData
		err error
	)
	err = json.Unmarshal(data, &c)
	if err != nil {
		return nil, fmt.Errorf("error unmarshaling inputData: %v", err)
	}
	return &c, nil
}

type outputDataCodec struct{}

func (c *outputDataCodec) Encode(value interface{}) ([]byte, error) {
	return json.Marshal(value)
}

func (c *outputDataCodec) Decode(data []byte) (interface{}, error) {
	var m outputData
	return &m, json.Unmarshal(data, &m)
}

func predict(t *inputData) []byte {
	jsonValue, err := json.Marshal(t)
	if err != nil {
		_ = fmt.Errorf("error unmarshaling inputData: %v", err)
	}
	requestBody := bytes.NewBuffer(jsonValue)
	res, err := http.Post(
		predictionURL,
		"application/json; charset=UTF-8",
		requestBody,
	)
	if err != nil {
		_ = fmt.Errorf("error in prediction request: %v", err)
		panic(err)
	}
	// close response body
	defer res.Body.Close()

	// read response data
	data, err := ioutil.ReadAll(res.Body)
	if err != nil {
		_ = fmt.Errorf("error parsing prediction request body: %v", err)
	}
	return data
}

func process(ctx goka.Context, msg interface{}) {
	var m outputData
	m.StreamingConsumeTimestamp = time.Now().UnixNano() / 1000000
	t := msg.(*inputData)
	publishTimestamp := ctx.Timestamp().UnixNano() / 1000000

	// call predict HTTP API
	tc := predict(t)

	err := json.Unmarshal(tc, &m)
	if err != nil {
		_ = fmt.Errorf("error unmarshaling outputData: %v", err)
	}
	m.PublishTimestamp = publishTimestamp

	ctx.Emit(outputTopic, "", &m)
	fmt.Printf("[proc] text: %s, msg: %v, subcategory: %s\n", t.Text, msg, m.Subcategory)
}

func runProcessor() {
	g := goka.DefineGroup(group,
		goka.Input(inputTopic, new(inputDataCodec), process),
		goka.Output(outputTopic, new(outputDataCodec)),
	)
	tmc := goka.NewTopicManagerConfig()
	tmc.Table.Replication = 1
	tmc.Stream.Replication = 1
	p, err := goka.NewProcessor(brokers,
		g,
		goka.WithTopicManagerBuilder(goka.TopicManagerBuilderWithTopicManagerConfig(tmc)),
		goka.WithConsumerGroupBuilder(goka.DefaultConsumerGroupBuilder),
	)
	if err != nil {
		panic(err)
	}

	ctx, cancel := context.WithCancel(context.Background())
	done := make(chan struct{})
	go func() {
		defer close(done)
		if err = p.Run(ctx); err != nil {
			fmt.Printf("error running processor: %v", err)
		}
	}()

	sigs := make(chan os.Signal)
	go func() {
		signal.Notify(sigs, syscall.SIGINT, syscall.SIGTERM, syscall.SIGKILL)
	}()

	select {
	case <-sigs:
		fmt.Println("sigs")
	case <-done:
		fmt.Println("done")
	}
	fmt.Println("canceling")
	cancel()
	<-done
	fmt.Println("terminated")
}

func main() {
	runProcessor()
}

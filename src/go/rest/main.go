package main

import (
	"encoding/json"
	"fmt"
	"io/ioutil"
	"math/rand"
	"net/http"
	"time"
	"os"
	"strconv"

	"github.com/go-playground/validator"
	"github.com/gorilla/mux"
	log "github.com/sirupsen/logrus"
)

// The HTTP API port number
const port int = 10000

// The maximum inference time of the predictions served in this API.
// The prediction duration will be generated randomly with this maximum value in ms.
var maxInferenceTimeMS

// use a single instance of Validate, it caches struct info
var validate *validator.Validate

// InputData contains the input data received in a prediction request
type InputData struct {
	UID  string `json:"uid"`
	Text string `json:"text"`
}

// OutputData provides the output data returned in a prediction response
type OutputData struct {
	UID         string  `json:"uid"`
	Text        string  `json:"text"`
	Category    string  `json:"category"`
	Subcategory string  `json:"subcategory"`
	Confidence  float32 `json:"confidence"`
	Model       string  `json:"model"`
	Version     int     `json:"version"`
}

// implements the /predict endpoint
func predict(w http.ResponseWriter, r *http.Request) {
	log.Debug("")
	body, err := ioutil.ReadAll(r.Body)
	if err != nil {
		log.Error(err)
	}

	var predictionInput InputData
	err = json.Unmarshal(body, &predictionInput)
	if err != nil {
		log.Error(err)
		http.Error(w, err.Error(), http.StatusBadRequest)
		return
	}

	// perform validation of the unmarshalled struct
	err = validate.Struct(&predictionInput)
	if err != nil {
		log.Error(err)
		http.Error(w, err.Error(), http.StatusUnprocessableEntity)
		return
	}

	log.Infof("Received the following text to categorize: %s", predictionInput.Text)

	// simulate inference duration
	inferenceTimeMS := rand.Intn(maxInferenceTimeMS)
	time.Sleep(time.Duration(inferenceTimeMS) * time.Millisecond)

	// write output data
	predictionOutput := OutputData{
		Text:        predictionInput.Text,
		UID:         "123",
		Category:    "1",
		Subcategory: "1",
		Confidence:  0.5,
		Model:       "model",
		Version:     1,
	}

	// encode predictionOuput into JSON and send to ResponseWriter
	json.NewEncoder(w).Encode(predictionOutput)
}

func main() {
	maxInferenceTimeMS = strconv.Atoi(os.Getenv("MAX_INFERENCE_TIME_MS"))

	address := fmt.Sprintf(":%d", port)
	log.Infof("Starting HTTP REST API at port %s ...", address)
	log.SetLevel(log.InfoLevel)

	// initialize validator
	validate = validator.New()

	// initialize router and add endpoints
	router := mux.NewRouter()
	router.HandleFunc("/predict", predict).Methods(http.MethodPost)

	// start http server
	log.Fatal(http.ListenAndServe(address, router))
}

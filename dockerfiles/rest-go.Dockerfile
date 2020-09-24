FROM golang:1.15

RUN go get github.com/go-playground/validator && \
    go get github.com/gorilla/mux && \
    go get github.com/sirupsen/logrus

COPY apis/go/rest /go/src/github.com/pedrodeoliveira/kafka-streaming-tests/src/go/rest

WORKDIR /go/src/app
COPY . .

RUN cd apis/go/rest && go build app/apis/go/rest
ENTRYPOINT ["/go/src/app/apis/go/rest/rest"]
EXPOSE 10000
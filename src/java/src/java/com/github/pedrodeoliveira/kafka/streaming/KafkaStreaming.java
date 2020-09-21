package com.github.pedrodeoliveira.kafka.streaming;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.JsonNodeFactory;
import com.fasterxml.jackson.databind.node.ObjectNode;
import org.apache.kafka.common.serialization.Deserializer;
import org.apache.kafka.common.serialization.Serde;
import org.apache.kafka.common.serialization.Serdes;
import org.apache.kafka.common.serialization.Serializer;
import org.apache.kafka.connect.json.JsonDeserializer;
import org.apache.kafka.connect.json.JsonSerializer;
import org.apache.kafka.streams.KafkaStreams;
import org.apache.kafka.streams.StreamsBuilder;
import org.apache.kafka.streams.StreamsConfig;
import org.apache.kafka.streams.kstream.Consumed;
import org.apache.kafka.streams.kstream.KStream;
import org.apache.kafka.streams.kstream.Produced;

import java.util.Properties;
import java.util.Random;

/**
 *
 * @author Pedro Oliveira
 */
public class KafkaStreaming {

	private static final String defaultBootstrapServers = "localhost:9092";

	public static void main(String[] args) {

		// Configure Kafka Streams Application
		String bootstrapServersOverride = System.getenv("BOOTSTRAP_SERVERS");
		final String bootstrapServers = bootstrapServersOverride != null ? bootstrapServersOverride: defaultBootstrapServers;
		final String inputTopic = System.getenv("KAFKA_INPUT_TOPIC");
		final String outputTopic = System.getenv("KAFKA_OUTPUT_TOPIC");

		final int maxInferenceTimeMs = Integer.parseInt(System.getenv("MAX_INFERENCE_TIME_MS"));

		final Properties streamsConfiguration = new Properties();

		// Give the Streams application a unique name. The name must be unique
		// in the Kafka cluster against which the application is run.
		final String GROUP_ID = "kafka-streams";
		streamsConfiguration.put(StreamsConfig.APPLICATION_ID_CONFIG, GROUP_ID);

		// Where to find Kafka broker(s).
		streamsConfiguration.put(StreamsConfig.BOOTSTRAP_SERVERS_CONFIG, bootstrapServers);

		final Serializer<JsonNode> jsonSerializer = new JsonSerializer();
		final Deserializer<JsonNode> jsonDeserializer = new JsonDeserializer();
		final Serde<JsonNode> jsonSerde = Serdes.serdeFrom(jsonSerializer, jsonDeserializer);

		// In the subsequent lines we define the processing topology of the Streams
		// application.
		final StreamsBuilder builder = new StreamsBuilder();

		// Specify default (de)serializers for record keys and for record
		// values.
		final Consumed<String, JsonNode> consumed = Consumed.with(Serdes.String(), jsonSerde);

		// Construct a `KStream` from the input topic, where
		final KStream<String, JsonNode> inputStream = builder.stream(inputTopic, consumed);

		KStream<String, JsonNode> outputStream = inputStream.
				mapValues(value -> {
					System.out.println("Received: " + value);
					final ObjectNode valueNode = JsonNodeFactory.instance.objectNode();
					valueNode.put("text", value.get("text").textValue());
					valueNode.put("uid", value.get("uid").textValue());
					valueNode.put("category", "10");
					valueNode.put("subcategory", "10");
					valueNode.put("confidence", 0.5);
					valueNode.put("model", "model");
					valueNode.put("version", 6);
					try {
						int inferenceTimeMs = new Random().nextInt(maxInferenceTimeMs);
						Thread.sleep(inferenceTimeMs);
					} catch (InterruptedException e) {
						e.printStackTrace();
					}
					return valueNode;
				});

		// Send transformed messages to Output Topic
		outputStream.to(outputTopic, Produced.with(Serdes.String(), jsonSerde));

		// Start Kafka Streams Application to process new incoming images from input topic
		final KafkaStreams streams = new KafkaStreams(builder.build(), streamsConfiguration);

		streams.cleanUp();
		streams.start();

		System.out.println("Kafka Streams (" + GROUP_ID + ") is running ...");
		System.out.println("Messages arrive at topic " + inputTopic + ", output messages are sent to " + outputTopic);

		// Add shutdown hook to respond to SIGTERM and gracefully close Kafka
		// Streams
		Runtime.getRuntime().addShutdownHook(new Thread(streams::close));
	}
}

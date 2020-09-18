import json
import logging

from kafka import KafkaConsumer
import os
import time

# kafka configs
KAFKA_TOPIC = os.getenv('KAFKA_TOPIC', 'input-topic')
KAFKA_BOOTSTRAP_SERVERS = os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'localhost:9092')

# log configuration
log_level = os.getenv('LOG_LEVEL', 'INFO')
logging.basicConfig(format='%(levelname)s:%(message)s', level=getattr(logging, log_level))
logger = logging.getLogger(__name__)


consumer: KafkaConsumer = None
counter = 0
start_time = time.time()
NBR_OF_MESSAGES = 10000


def start_consuming():
    global counter
    for msg in consumer:
        logger.debug(f"consumed: {msg}")
        topic = msg.topic
        data = json.loads(msg.value)
        logger.debug(f"topic {topic} data: {data}")
        counter += 1
        # time.sleep(0.015)
        if counter >= NBR_OF_MESSAGES:
            break
    elapsed_time = time.time() - start_time
    print(f'Read {counter} messages in {elapsed_time:.2f} seconds')
    consumer.close()


if __name__ == "__main__":
    consumer = KafkaConsumer(KAFKA_TOPIC, bootstrap_servers=[KAFKA_BOOTSTRAP_SERVERS],
                             enable_auto_commit=True, group_id='kafka-python')

    # 2. start consuming messages
    start_consuming()

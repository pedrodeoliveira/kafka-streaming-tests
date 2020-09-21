#!/usr/bin/env python
import asyncio
import logging
import faust
import os
from random import randint

from common import generate_random_output_message

# kafka configs
KAFKA_INPUT_TOPIC = os.getenv('KAFKA_INPUT_TOPIC', 'input-topic')
KAFKA_OUTPUT_TOPIC = os.getenv('KAFKA_OUTPUT_TOPIC', 'output-topic')
KAFKA_BOOTSTRAP_SERVERS = os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'localhost:9092')

# log configuration
log_level = os.getenv('LOG_LEVEL', 'INFO')
logging.basicConfig(format='%(levelname)s:%(message)s', level=getattr(logging, log_level))
logger = logging.getLogger(__name__)

# agents' configs
CONCURRENCY = int(os.getenv('CONCURRENCY', 200))

# initialize Faust App
app = faust.App('streaming_faust', broker=f'kafka://{KAFKA_BOOTSTRAP_SERVERS}')


class InputData(faust.Record):
    uid: str
    text: str


class OutputData(faust.Record):
    uid: str
    text: str
    category: str
    subcategory: str
    confidence: float
    model: str
    version: int
    publish_ts: int
    streaming_consume_ts: int


# create topics
input_topic = app.topic(KAFKA_INPUT_TOPIC, value_type=InputData)
output_topic = app.topic(KAFKA_OUTPUT_TOPIC, value_type=OutputData)


@app.agent(input_topic, concurrency=CONCURRENCY)
async def process_event(stream):
    async for event in stream.events():
        value = event.value
        key = event.key.decode('utf-8')
        logger.debug(f'received event with key: {key} and value: {value}')

        publish_ts = (event.message.timestamp * 1000)
        value_dict = value.asdict()
        output_data = generate_random_output_message(value_dict, publish_ts)
        random_inference_time_ms = randint(0, 50)
        logger.debug(f'inference_time_ms: {random_inference_time_ms}')
        await asyncio.sleep(random_inference_time_ms / 1000)

        output_msg = OutputData(**output_data)
        await output_topic.send(key=key, value=output_msg)


if __name__ == '__main__':
    app.main()

#!/usr/bin/env python
import logging
import time

import aiohttp
import faust
import os


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

# url of the http service
HTTP_URL = os.getenv('HTTP_URL', 'http://localhost:8000/svc')

# initialize Faust App
app = faust.App('streaming_faust_aiohttp', broker=f'kafka://{KAFKA_BOOTSTRAP_SERVERS}')


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
    session = aiohttp.ClientSession()
    async for event in stream.events():
        value = event.value
        key = event.key.decode('utf-8')
        logger.debug(f'received event with key: {key} and value: {value}')
        publish_ts = (event.message.timestamp * 1000)
        streaming_consume_ts = round(time.time() * 1000)

        # run inference
        value_dict = value.asdict()
        post_result = await session.post(HTTP_URL, json=value_dict)
        if post_result.status != 200:
            logger.error(f'failed request for {value_dict}')
            continue

        # get result and add timestamp data
        result = await post_result.json()
        logger.debug(f'received api result: {result}')
        result['publish_ts'] = publish_ts
        result['streaming_consume_ts'] = streaming_consume_ts

        # publish results to output topic
        output_msg = OutputData(**result)
        await output_topic.send(key=key, value=output_msg)


if __name__ == '__main__':
    app.main()

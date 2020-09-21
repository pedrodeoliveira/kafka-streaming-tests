import time

from aiokafka import AIOKafkaProducer
import asyncio
import json
import os

from common import generate_random_input_message

loop = asyncio.get_event_loop()

# kafka configs
KAFKA_BOOTSTRAP_SERVERS = os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'localhost:9092')
KAFKA_TOPIC = os.getenv('KAFKA_TOPIC', 'input-topic')


async def send_one():
    producer = AIOKafkaProducer(loop=loop, bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS)
    # Get cluster layout and initial topic/partition leadership information
    await producer.start()
    try:
        # Produce message
        value = generate_random_input_message()
        key = value['uid'].encode('utf-8')
        value_json = json.dumps(value).encode('utf-8')
        print(time.time())
        await producer.send(KAFKA_TOPIC, value_json, key=key)
    finally:
        # Wait for all pending messages to be delivered or expire.
        await producer.stop()

loop.run_until_complete(send_one())

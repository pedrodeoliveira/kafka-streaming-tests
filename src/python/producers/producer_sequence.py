import logging

from aiokafka import AIOKafkaProducer
import asyncio
import json
import os

from common import generate_random_input_message


# kafka configs
KAFKA_TOPIC = os.getenv('KAFKA_TOPIC', 'input-topic')
KAFKA_BOOTSTRAP_SERVERS = os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'localhost:9092')

# log configuration
log_level = os.getenv('LOG_LEVEL', 'INFO')
logging.basicConfig(format='%(levelname)s:%(message)s', level=getattr(logging, log_level))
logger = logging.getLogger(__name__)

# requested throughput (msgs/s)
NUMBER_OF_MSGS_PER_SECOND = int(os.getenv('NUMBER_OF_MSGS_PER_SECOND', '40'))

# global kafka producer
producer: AIOKafkaProducer = None


async def start_producer():
    # get cluster layout and initial topic/partition leadership information
    await producer.start()
    sleep_time_secs = 1 / NUMBER_OF_MSGS_PER_SECOND
    logger.info(f'Requested msgs/s: {NUMBER_OF_MSGS_PER_SECOND} '
                f'Sleep time (ms): {sleep_time_secs*1000:.2f}')
    while True:
        await send_one()
        await asyncio.sleep(sleep_time_secs)


async def send_one():
    try:
        # Produce message
        value = generate_random_input_message()
        key = value['uid'].encode('utf-8')
        value_json = json.dumps(value).encode('utf-8')
        logger.debug(f'sending msg with key: {value["uid"]} and value: {value}')
        await producer.send(KAFKA_TOPIC, value_json, key=key)
    except Exception as e:
        logger.error(e)
        # Wait for all pending messages to be delivered or expire.
        await producer.stop()


loop = asyncio.get_event_loop()
producer = AIOKafkaProducer(loop=loop, bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS)
loop.run_until_complete(start_producer())
loop.close()

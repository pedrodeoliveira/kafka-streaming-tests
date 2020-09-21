import asyncio
import json
import logging
import random
import os
from aiokafka.producer import AIOKafkaProducer

from common import generate_random_input_message

# kafka configs
KAFKA_TOPIC = os.getenv('KAFKA_TOPIC', 'input-topic')
KAFKA_BOOTSTRAP_SERVERS = os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'localhost:9092')

# log configuration
log_level = os.getenv('LOG_LEVEL', 'INFO')
logging.basicConfig(format='%(levelname)s:%(message)s', level=getattr(logging, log_level))
logger = logging.getLogger(__name__)

# requested throughput (msgs/s)
NUMBER_OF_MESSAGES = int(os.getenv('NUMBER_OF_MESSAGES', '40'))
NUMBER_OF_SECONDS = int(os.getenv('NUMBER_OF_SECONDS', '1'))


async def start_producer(loop):
    logger.info(f'Starting producer with throughput of {NUMBER_OF_MESSAGES} messages per '
                f'{NUMBER_OF_SECONDS} second(s)')
    while True:
        await send_many(NUMBER_OF_MESSAGES, loop)
        logger.debug(f'Batch sent, sleeping {NUMBER_OF_SECONDS} second(s)')
        await asyncio.sleep(NUMBER_OF_SECONDS)


async def send_many(num, loop):
    topic = KAFKA_TOPIC
    producer = AIOKafkaProducer(loop=loop, bootstrap_servers=[KAFKA_BOOTSTRAP_SERVERS])
    await producer.start()

    batch = producer.create_batch()

    i = 0
    while i < num:
        msg_data = generate_random_input_message()
        key = msg_data['uid'].encode('utf-8')
        msg = json.dumps(msg_data).encode("utf-8")
        metadata = batch.append(key=key, value=msg, timestamp=None)
        if metadata is None:
            partitions = await producer.partitions_for(topic)
            partition = random.choice(tuple(partitions))
            await producer.send_batch(batch, topic, partition=partition)
            logger.info(f"{batch.record_count()} messages sent to partition {partition}")
            batch = producer.create_batch()
            continue
        i += 1
    partitions = await producer.partitions_for(topic)
    partition = random.choice(tuple(partitions))
    await producer.send_batch(batch, topic, partition=partition)
    logger.info(f"{batch.record_count()} messages sent to partition {partition}")
    await producer.stop()


loop = asyncio.get_event_loop()
loop.run_until_complete(start_producer(loop))
loop.close()

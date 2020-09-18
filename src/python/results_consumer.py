import json
import logging

from kafka import KafkaConsumer
import os
import time
import random

import sqlite3

# kafka configs
KAFKA_TOPIC = os.getenv('KAFKA_TOPIC', 'output-topic')
KAFKA_BOOTSTRAP_SERVERS = os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'localhost:9092')

# log configuration
log_level = os.getenv('LOG_LEVEL', 'INFO')
logging.basicConfig(format='%(levelname)s:%(message)s', level=getattr(logging, log_level))
logger = logging.getLogger(__name__)


consumer: KafkaConsumer = None
RUN_ID = int(os.getenv('RUN_ID', random.randint(0, 1000000)))

SQLITE_PATH = os.getenv('SQLITE_PATH')
DB = sqlite3.connect(SQLITE_PATH)


def start_consuming():
    for msg in consumer:
        logger.debug(f"Consumed: {msg}")
        consume_ts = round(time.time()*1000)
        streaming_publish_ts = msg.timestamp
        data = json.loads(msg.value)

        # skip messages if they don't have a publish_ts (old messages)
        if 'publish_ts' not in data or 'streaming_consume_ts' not in data:
            logger.warning('skipping old message')
            continue

        # calculate elapsed times
        pub_to_stream_time_ms = data['streaming_consume_ts'] - data['publish_ts']
        inference_time_ms = streaming_publish_ts - data['streaming_consume_ts']
        stream_to_cons_time_ms = consume_ts - streaming_publish_ts
        total_time_ms = pub_to_stream_time_ms + inference_time_ms + stream_to_cons_time_ms

        # build inference results dict
        output_data = {
            'run_id': RUN_ID,
            'uid': data['uid'],
            'publish_ts': data['publish_ts'],
            'streaming_consume_ts': data['streaming_consume_ts'],
            'streaming_publish_ts': streaming_publish_ts,
            'consume_ts': consume_ts,
            'pub_to_stream_time_ms': pub_to_stream_time_ms,
            'inference_time_ms': inference_time_ms,
            'stream_to_cons_time_ms': stream_to_cons_time_ms,
            'total_time_ms': total_time_ms
        }

        # insert into database and commit
        DB.execute("INSERT INTO results values "
                   "(:run_id,:uid,:publish_ts,:streaming_consume_ts,"
                   ":streaming_publish_ts,:consume_ts,:pub_to_stream_time_ms,"
                   ":inference_time_ms,:stream_to_cons_time_ms,:total_time_ms)",
                   output_data)
        DB.commit()
        logger.debug('committed')


if __name__ == "__main__":
    consumer = KafkaConsumer(KAFKA_TOPIC, bootstrap_servers=[KAFKA_BOOTSTRAP_SERVERS],
                             enable_auto_commit=True, group_id='results-consumer')

    # 2. start consuming messages
    logger.info(f'Starting run {RUN_ID} ...')
    start_consuming()

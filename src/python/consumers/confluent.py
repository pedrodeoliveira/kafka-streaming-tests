import json

from confluent_kafka import Consumer
import time
import os

KAFKA_TOPIC = os.getenv('KAFKA_TOPIC', 'input-topic')

settings = {
    'bootstrap.servers': 'localhost:9092',
    'group.id': 'confluent',
    'client.id': 'client-1',
    'enable.auto.commit': True,
    'session.timeout.ms': 6000,
    'api.version.request': False,
    'default.topic.config': {'auto.offset.reset': 'smallest'}
}

c = Consumer(settings)

c.subscribe([KAFKA_TOPIC])
consume_time = time.time()
msg_count = 0

try:
    while msg_count < 10000:
        msg = c.poll(0.1)
        if msg is None:
            continue
        if msg.error():
            print(f'Error occurred: {msg.error().str()}')
            continue
        msg_count += 1
        data = json.loads(msg.value().decode('utf-8'))
        # time.sleep(0.015)
        # print(data)
        elapsed_time = time.time() - consume_time
    print(f'Read {msg_count} messages from {msg.topic()}-{msg.partition()} in '
          f'{elapsed_time:.2f} seconds')
except KeyboardInterrupt:
    pass
finally:
    c.close()

from confluent_kafka import Producer, Consumer, KafkaError
import time

p = Producer({'bootstrap.servers': 'localhost:9092', 'api.version.request': False})
start_time = time.time()
try:
    for val in range(0, 10000):
        p.produce('newtwo5', 'myvalue #{0}'.format(val))
except KeyboardInterrupt:
    pass

print("Processed 10000 messsages in {0:.2f} seconds".format(time.time() - start_time))

p.flush(30)

settings = {
    'bootstrap.servers': 'localhost:9092',
    'group.id': 'mygroup',
    'client.id': 'client-1',
    'enable.auto.commit': True,
    'session.timeout.ms': 6000,
    'api.version.request': False,
    'default.topic.config': {'auto.offset.reset': 'smallest'}
}

c = Consumer(settings)

c.subscribe(['newtwo5'])
consume_time = time.time()
msgcount = 0
try:
    while msgcount < 10000:
        msg = c.poll(0.1)
        if msg is None:
            continue
        if msg.error():
            print('Error occured: {0}'.format(msg.error().str()))
            continue
        msgcount += 1
    print('Read {0} msessages from {1}-{2} in {3:.2f} seconds'
          .format(msgcount, msg.topic(), msg.partition(), time.time() - consume_time))
except KeyboardInterrupt:
    pass
finally:
    c.close()
    print('End to End time: {}'.format(time.time() - start_time))

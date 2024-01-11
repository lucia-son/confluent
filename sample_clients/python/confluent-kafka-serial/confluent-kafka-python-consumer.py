from confluent_kafka import Consumer

c = Consumer({
    'bootstrap.servers': '192.168.64.42:9092',
    'group.id': '02decoding_test',
    'auto.offset.reset': 'earliest'
})

c.subscribe(['orcl.C__CONFLUENT.ACTORS.CHARACTER.KR'])

while True:
    msg = c.poll(1.0)

    if msg is None:
        continue
    if msg.error():
        print("Consumer error: {}".format(msg.error()))
        continue

    print('Received message: {}'.format(msg.value()))
    print('Received message: {}'.format(msg.value().decode('euc-kr')))

c.close()

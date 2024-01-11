#  consumer.py
from kafka import KafkaConsumer
from google.protobuf import request_pb2
import requests 

rq = request_pb2.Request

# topic, broker list
consumer = KafkaConsumer(
        'orcl.C__CONFLUENT.ACTORS.CHARACTER.KR',
        bootstrap_servers=['data02.young.com:9092'],
        auto_offset_reset='earliest',
        enable_auto_commit=True,
        group_id='encodingtest02',
        consumer_timeout_ms=1000
    )


# consumer list를 가져온다
print('[begin] get consumer list')
while True:
    for message in consumer:
        new_value=rq.ParseFromString(message.value)
        print("Topic: %s, Partition: %d, Offset: %d, Key: %s, Value: %s" % (
                    message.topic, message.partition, message.offset, message.key, new_value
                        ))
    print('[end] get consumer list')

# 3rd party library imported
from confluent_kafka import SerializingProducer
from confluent_kafka.schema_registry import SchemaRegistryClient
from confluent_kafka.schema_registry.avro import AvroSerializer
from confluent_kafka.schema_registry import Schema
#from constants import schema_str

#from kafka import KafkaProducer
import requests
import json
from collections import OrderedDict 

import time
import logging
import time

from enum import Enum
import random as rd 

json_data = OrderedDict()

class State(Enum):
   Pending = 1 
   Processing = 2
   Completed = 3
   Canceled = 4 
   Unknown = 5 

status_names = [status.name for status in State]

kafka_url = '192.168.137.105:30092'
schema_registry_url = 'http://192.168.137.105:30881'
kafka_topic = 'order' 
schema_registry_subject = f"{kafka_topic}-value"

def delivery_report(errmsg, msg):
    if errmsg is not None:
        print("Delivery failed for Message: {} : {}".format(msg.key(), errmsg))
        return
    print('Message: {} successfully produced to Topic: {} Partition: [{}] at offset {}'.format(msg.key(), msg.topic(), msg.partition(), msg.offset()))

def avro_producer(kafka_url, schema_registry_url, schema_registry_subject):
    # schema registry
    sr, latest_version = get_schema_from_schema_registry(schema_registry_url, schema_registry_subject)
    print("in avro_producer def, this is get_schema_from_schema_registry")
    value_avro_serializer = AvroSerializer(schema_registry_client = sr,
                                          schema_str = latest_version.schema.schema_str,
                                          conf={
                                              'auto.register.schemas': False  }
                                          )
    print("value_avro_serializer passed")

    # Kafka Producer
    producer = SerializingProducer({
        'bootstrap.servers': kafka_url,
        'security.protocol': 'plaintext',
        'value.serializer': value_avro_serializer,
        'delivery.timeout.ms': 120000, 
        'enable.idempotence': 'true'
    })

    for sequence in range (5):
          now = int(time.time())
          state = rd.choice(list(status_names))

          json_data["orderId"] = sequence
          json_data["customerId"] = sequence
          json_data["totalPriceCents"] = sequence * 100
          json_data["state"] = state
          json_data["timestamp"] = now

          message_json = json.dumps(json_data, ensure_ascii=False, indent = "\t")
          print (message_json)          
                
          try:
               # print(decoded_line + '\n')
               producer.produce(topic=kafka_topic, value=message_json, on_delivery=delivery_report)
               print("produce try")
               # Trigger any available delivery report callbacks from previous produce() calls
               events_processed = producer.poll(1)
               print(f"events_processed: {events_processed}")

               messages_in_queue = producer.flush(1)
               print(f"messages_in_queue: {messages_in_queue}")
               
          except Exception as e:
               print("exception")
               print(e)
                        
def get_schema_from_schema_registry(schema_registry_url, schema_registry_subject):
    sr = SchemaRegistryClient({'url': schema_registry_url})
    latest_version = sr.get_latest_version(schema_registry_subject)
    print ("this is get_schema_from_schema_registry")
    return sr, latest_version

def register_schema(schema_registry_url, schema_registry_subject, schema_str):
    sr = SchemaRegistryClient({'url': schema_registry_url})
    schema = Schema(schema_str, schema_type="AVRO")
    schema_id = sr.register_schema(subject_name=schema_registry_subject, schema=schema)
    print("this is register_schema")
    return schema_id

def update_schema(schema_registry_url, schema_registry_subject, schema_str):
    sr = SchemaRegistryClient({'url': schema_registry_url})
    versions_deleted_list = sr.delete_subject(schema_registry_subject)
    print(f"versions of schema deleted list: {versions_deleted_list}")

    schema_id = register_schema(schema_registry_url, schema_registry_subject, schema_str)
    return schema_id
                        
avro_producer(kafka_url, schema_registry_url, schema_registry_subject)


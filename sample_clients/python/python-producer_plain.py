from string import Template
from kafka import KafkaProducer
import threading
import logging 
import signal
import datetime
import os
from krbcontext.context import krbContext

logging.basicConfig(filename='./testProducer.log', level = logging.INFO)

def handle_sigterm(*args):
  raise KeyboardInterrupt()

class MessageProducer:
  config = {}
  topic = ''
  producer = ''
  sequence = 1

  def __init__(self, config, topic): 
    self.config = config
    self.topic = topic 
    self.producer = KafkaProducer(**self.config)

  def sendMessage(self, message):
    logging.info('SENDING MESSAGES!...')
    self.producer.send(topic,message).add_callback(self.on_send_success).add_errback(self.on_send_error)
    self.producer.flush()

  def on_send_success(self,record_metadata):
    logging.info('topic={t}, partition={p},offset={o}'.format(t = record_metadata.topic, p = record_metadata.partition, o = record_metadata.offset))

  def on_send_error(self,excp):
    logging.error('i am an errback', exc_info=excp)

  def sendDummyMessage(self):
    next = self.sequence
    now = datetime.datetime.now()
    self.sequence = self.sequence + 1 
    nextDummyMessage = Template('{"sequence": $sequence, "name": "pythonTestProducer-$sequence","created": "$created"}').substitute(sequence=next, created=now) 
    self.sendMessage(bytes(nextDummyMessage,encoding = 'utf-8'))
    threading.Timer(1, self.sendDummyMessage).start() 

logging.info('Service Start ! ')

signal.signal(signal.SIGTERM, handle_sigterm)

topic = 'subscriptions'

producer_config = {
    'bootstrap_servers':['192.168.137.101:9092','192.168.137.102:9092','192.168.137.103:9092'],
    'max_block_ms': 2400000,
    'api_version':(3,4,0),
    'acks':'all'
} 

producer = MessageProducer(producer_config, topic)
producer.sendDummyMessage()
            
logging.info('Service End ! ')

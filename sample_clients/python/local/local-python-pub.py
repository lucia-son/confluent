from string import Template
from kafka import KafkaProducer
import threading
import logging
import signal
import datetime
import os
from krbcontext.context import krbContext

logging.basicConfig(filename='./testProducer.log', level = logging.DEBUG)

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

topic = 'pythonTest'
principal = 'confluent_c3@KAFKA.SECURE'
keytab_file = '/home/confluent/pythontest/confluent_c3.keytab'

producer_config = {
    'bootstrap_servers':['tester102:9092','tester103:9092','tester104:9092'],
    'security_protocol':'SASL_PLAINTEXT',
    'sasl_mechanism':'GSSAPI',
    'sasl_kerberos_service_name':'kafka',
    'api_version':(2,6,0),
    'acks':'all'
}
with krbContext (using_keytab = True,
                 principal = principal,
                 keytab_file = keytab_file):
    pass

producer = MessageProducer(producer_config, topic)
producer.sendDummyMessage()

logging.info('Service End ! ')

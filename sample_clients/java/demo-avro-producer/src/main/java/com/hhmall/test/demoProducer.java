package com.hhmall.test;

import org.apache.kafka.clients.producer.KafkaProducer;
import org.apache.kafka.clients.producer.Producer;
import org.apache.kafka.clients.producer.ProducerConfig;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.util.Properties;

public class demoProducer {

    private final static Logger logger = LoggerFactory.getLogger(demoProducer.class.getName());

    public static void main(String[] args) {

        String bootstrapServers = "192.168.137.101:9092";
        String sourceTopic = "SPLUNK_HF_DATA";
        String targetTopic = "SPLUNK_PREPROCESSED";

        Properties producerProps = new Properties();

        producerProps.put(ProducerConfig.BOOTSTRAP_SERVERS_CONFIG, bootstrapServers);
        producerProps.put(ProducerConfig.KEY_SERIALIZER_CLASS_CONFIG, StringDeSerializer.class.getName());
        producerProps.put(ProducerConfig.VALUE_SERIALIZER_CLASS_CONFIG, StringDeSerializer.class.getName());
        KafkaProducer<String, String> producer = new KafkaProducer<String, String>(producerProps);

        Producer<String, Object> producer = new KafkaProducer<String, Object>(producer props);


    }
}
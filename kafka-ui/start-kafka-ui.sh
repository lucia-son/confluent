#!/bin/bash

ENGINE_HOME="/app/kafka-ui"
PROCESS_NAME="kafkaUI"

LOG_DIR="${ENGINE_HOME}/logs"
export LOG_DIR

nohup /usr/lib/jvm/jdk-17-oracle-x64/bin/java -Xms4096m -Xmx4096m -Dsun.rmi.transport.tcp.responseTimeout=60000  -Dspring.config.additional-location=${ENGINE_HOME}/application.yml --add-opens java.rmi/javax.rmi.ssl=ALL-UNNAMED -jar ${ENGINE_HOME}/kafka-ui-api-v0.7.0.jar  >${LOG_DIR}/kafka_ui.log  2>&1 &

tail -f ${LOG_DIR}/kafka_ui.log

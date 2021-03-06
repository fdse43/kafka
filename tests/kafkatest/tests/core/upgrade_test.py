# Licensed to the Apache Software Foundation (ASF) under one or more
# contributor license agreements.  See the NOTICE file distributed with
# this work for additional information regarding copyright ownership.
# The ASF licenses this file to You under the Apache License, Version 2.0
# (the "License"); you may not use this file except in compliance with
# the License.  You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from ducktape.mark import parametrize
from ducktape.mark.resource import cluster
from ducktape.utils.util import wait_until
from kafkatest.services.console_consumer import ConsoleConsumer
from kafkatest.services.kafka import KafkaService
from kafkatest.services.kafka import config_property
from kafkatest.services.verifiable_producer import VerifiableProducer
from kafkatest.services.zookeeper import ZookeeperService
from kafkatest.tests.produce_consume_validate import ProduceConsumeValidateTest
from kafkatest.utils import is_int
from kafkatest.version import LATEST_0_8_2, LATEST_0_9, LATEST_0_10, LATEST_0_10_0, LATEST_0_10_1, LATEST_0_10_2, LATEST_0_11_0, LATEST_1_0, LATEST_1_1, LATEST_2_0, LATEST_2_1, LATEST_2_2, LATEST_2_3, LATEST_2_4, V_0_9_0_0, V_0_11_0_0, DEV_BRANCH, KafkaVersion
from kafkatest.services.kafka.util import java_version, new_jdk_not_supported

class TestUpgrade(ProduceConsumeValidateTest):

    def __init__(self, test_context):
        super(TestUpgrade, self).__init__(test_context=test_context)

    def setUp(self):
        self.topic = "test_topic"
        self.partitions = 3
        self.replication_factor = 3
        self.zk = ZookeeperService(self.test_context, num_nodes=1)
        self.zk.start()

        # Producer and consumer
        self.producer_throughput = 1000
        self.num_producers = 1
        self.num_consumers = 1

    def wait_until_rejoin(self):
        for partition in range(0, self.partitions):
            wait_until(lambda: len(self.kafka.isr_idx_list(self.topic, partition)) == self.replication_factor, timeout_sec=60,
                    backoff_sec=1, err_msg="Replicas did not rejoin the ISR in a reasonable amount of time")

    def perform_upgrade(self, from_kafka_version, to_message_format_version=None):
        self.logger.info("First pass bounce - rolling upgrade")
        for node in self.kafka.nodes:
            self.kafka.stop_node(node)
            node.version = DEV_BRANCH
            node.config[config_property.INTER_BROKER_PROTOCOL_VERSION] = from_kafka_version
            node.config[config_property.MESSAGE_FORMAT_VERSION] = from_kafka_version
            self.kafka.start_node(node)
            self.wait_until_rejoin()

        self.logger.info("Second pass bounce - remove inter.broker.protocol.version config")
        for node in self.kafka.nodes:
            self.kafka.stop_node(node)
            del node.config[config_property.INTER_BROKER_PROTOCOL_VERSION]
            if to_message_format_version is None:
                del node.config[config_property.MESSAGE_FORMAT_VERSION]
            else:
                node.config[config_property.MESSAGE_FORMAT_VERSION] = to_message_format_version
            self.kafka.start_node(node)
            self.wait_until_rejoin()

    @cluster(num_nodes=6)
    @parametrize(from_kafka_version=str(LATEST_2_4), to_message_format_version=None, compression_types=["none"])
    @parametrize(from_kafka_version=str(LATEST_2_4), to_message_format_version=None, compression_types=["zstd"])
    @parametrize(from_kafka_version=str(LATEST_2_3), to_message_format_version=None, compression_types=["none"])
    @parametrize(from_kafka_version=str(LATEST_2_3), to_message_format_version=None, compression_types=["zstd"])
    @parametrize(from_kafka_version=str(LATEST_2_2), to_message_format_version=None, compression_types=["none"])
    @parametrize(from_kafka_version=str(LATEST_2_2), to_message_format_version=None, compression_types=["zstd"])
    @parametrize(from_kafka_version=str(LATEST_2_1), to_message_format_version=None, compression_types=["none"])
    @parametrize(from_kafka_version=str(LATEST_2_1), to_message_format_version=None, compression_types=["lz4"])
    @parametrize(from_kafka_version=str(LATEST_2_0), to_message_format_version=None, compression_types=["none"])
    @parametrize(from_kafka_version=str(LATEST_2_0), to_message_format_version=None, compression_types=["snappy"])
    @parametrize(from_kafka_version=str(LATEST_1_1), to_message_format_version=None, compression_types=["none"])
    @parametrize(from_kafka_version=str(LATEST_1_1), to_message_format_version=None, compression_types=["lz4"])
    @parametrize(from_kafka_version=str(LATEST_1_0), to_message_format_version=None, compression_types=["none"])
    @parametrize(from_kafka_version=str(LATEST_1_0), to_message_format_version=None, compression_types=["snappy"])
    @parametrize(from_kafka_version=str(LATEST_0_11_0), to_message_format_version=None, compression_types=["gzip"])
    @parametrize(from_kafka_version=str(LATEST_0_11_0), to_message_format_version=None, compression_types=["lz4"])
    @parametrize(from_kafka_version=str(LATEST_0_10_2), to_message_format_version=str(LATEST_0_9), compression_types=["none"])
    @parametrize(from_kafka_version=str(LATEST_0_10_2), to_message_format_version=str(LATEST_0_10), compression_types=["snappy"])
    @parametrize(from_kafka_version=str(LATEST_0_10_2), to_message_format_version=None, compression_types=["none"])
    @parametrize(from_kafka_version=str(LATEST_0_10_2), to_message_format_version=None, compression_types=["lz4"])
    @parametrize(from_kafka_version=str(LATEST_0_10_1), to_message_format_version=None, compression_types=["lz4"])
    @parametrize(from_kafka_version=str(LATEST_0_10_1), to_message_format_version=None, compression_types=["snappy"])
    @parametrize(from_kafka_version=str(LATEST_0_10_0), to_message_format_version=None, compression_types=["snappy"])
    @parametrize(from_kafka_version=str(LATEST_0_10_0), to_message_format_version=None, compression_types=["lz4"])
    @cluster(num_nodes=7)
    @parametrize(from_kafka_version=str(LATEST_0_9), to_message_format_version=None, compression_types=["none"], security_protocol="SASL_SSL")
    @cluster(num_nodes=6)
    @parametrize(from_kafka_version=str(LATEST_0_9), to_message_format_version=None, compression_types=["snappy"])
    @parametrize(from_kafka_version=str(LATEST_0_9), to_message_format_version=None, compression_types=["lz4"])
    @parametrize(from_kafka_version=str(LATEST_0_9), to_message_format_version=str(LATEST_0_9), compression_types=["none"])
    @parametrize(from_kafka_version=str(LATEST_0_9), to_message_format_version=str(LATEST_0_9), compression_types=["lz4"])
    @cluster(num_nodes=7)
    @parametrize(from_kafka_version=str(LATEST_0_8_2), to_message_format_version=None, compression_types=["none"])
    @parametrize(from_kafka_version=str(LATEST_0_8_2), to_message_format_version=None, compression_types=["snappy"])
    def test_upgrade(self, from_kafka_version, to_message_format_version, compression_types,
                     security_protocol="PLAINTEXT"):
        """Test upgrade of Kafka broker cluster from various versions to the current version

        from_kafka_version is a Kafka version to upgrade from

        If to_message_format_version is None, it means that we will upgrade to default (latest)
        message format version. It is possible to upgrade to 0.10 brokers but still use message
        format version 0.9

        - Start 3 node broker cluster on version 'from_kafka_version'
        - Start producer and consumer in the background
        - Perform two-phase rolling upgrade
            - First phase: upgrade brokers to 0.10 with inter.broker.protocol.version set to
            from_kafka_version and log.message.format.version set to from_kafka_version
            - Second phase: remove inter.broker.protocol.version config with rolling bounce; if
            to_message_format_version is set to 0.9, set log.message.format.version to
            to_message_format_version, otherwise remove log.message.format.version config
        - Finally, validate that every message acked by the producer was consumed by the consumer
        """
        self.kafka = KafkaService(self.test_context, num_nodes=3, zk=self.zk,
                                  version=KafkaVersion(from_kafka_version),
                                  topics={self.topic: {"partitions": self.partitions,
                      "replication-factor": self.replication_factor,
                      'configs': {"min.insync.replicas": 2}}})
        self.kafka.security_protocol = security_protocol
        self.kafka.interbroker_security_protocol = security_protocol

        jdk_version = java_version(self.kafka.nodes[0])

        if jdk_version > 9 and from_kafka_version in new_jdk_not_supported:
            self.logger.info("Test ignored! Kafka " + from_kafka_version + " not support jdk " + str(jdk_version))
            return

        self.kafka.start()

        self.producer = VerifiableProducer(self.test_context, self.num_producers, self.kafka,
                                           self.topic, throughput=self.producer_throughput,
                                           message_validator=is_int,
                                           compression_types=compression_types,
                                           version=KafkaVersion(from_kafka_version))

        if from_kafka_version <= LATEST_0_10_0:
            assert self.kafka.cluster_id() is None

        # With older message formats before KIP-101, message loss may occur due to truncation
        # after leader change. Tolerate limited data loss for this case to avoid transient test failures.
        self.may_truncate_acked_records = False if from_kafka_version >= V_0_11_0_0 else True

        new_consumer = from_kafka_version >= V_0_9_0_0
        # TODO - reduce the timeout
        self.consumer = ConsoleConsumer(self.test_context, self.num_consumers, self.kafka,
                                        self.topic, new_consumer=new_consumer, consumer_timeout_ms=30000,
                                        message_validator=is_int, version=KafkaVersion(from_kafka_version))

        self.run_produce_consume_validate(core_test_action=lambda: self.perform_upgrade(from_kafka_version,
                                                                                        to_message_format_version))

        cluster_id = self.kafka.cluster_id()
        assert cluster_id is not None
        assert len(cluster_id) == 22

        assert self.kafka.check_protocol_errors(self)

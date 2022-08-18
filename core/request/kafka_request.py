from typing import Dict

from confluent_kafka.cimpl import Message as KafkaMessage
from core.mq.kafka.kafka_publisher import KafkaPublisher
from core.request.base_request import BaseRequest
from core.logging.logger_utils import log
import core.logging.logger_constants as log_const


class KafkaRequest(BaseRequest):
    TOPIC_KEY = "topic_key"
    KAFKA_KEY = "kafka_key"
    TOPIC = "topic"

    def __init__(self, items, id=None):
        super(KafkaRequest, self).__init__(items)
        items = items or {}
        self.topic_key = items.get(self.TOPIC_KEY)
        self.kafka_key = items.get(self.KAFKA_KEY)
        # topic_key has priority over topic
        self.topic = items.get(self.TOPIC)

    def update_empty_items(self, items: Dict[str, str]):
        self.topic_key = self.topic_key or items.get(self.TOPIC_KEY)
        self.kafka_key = self.kafka_key or items.get(self.KAFKA_KEY)
        self.topic = self.topic or items.get(self.TOPIC)

    @property
    def group_key(self):
        return "{}_{}".format(self.kafka_key, self.topic_key) if (self.topic_key and self.kafka_key) else None

    def _get_new_headers(self, source_mq_message: KafkaMessage):
        headers = source_mq_message.headers() or []
        return headers

    def send(self, data, publisher: KafkaPublisher, source_mq_message):
        headers = self._get_new_headers(source_mq_message)
        if self.topic_key is not None:
            publisher.send(data, source_mq_message.key(), self.topic_key, headers=headers)
        elif self.topic is not None:
            publisher.send_to_topic(data, source_mq_message.key(), self.topic, headers=headers)
        else:
            log_params = {
                "data": str(data),
                log_const.KEY_NAME: log_const.EXCEPTION_VALUE
            }
            log("KafkaRequest: got no topic and no topic_key", params=log_params, level="ERROR")

    def run(self, data, params):
        publishers = params["publishers"]
        publisher = publishers[self.kafka_key]
        self.send(data=data, publisher=publisher, source_mq_message=params["mq_message"])

    def __str__(self):
        if self.topic_key is not None:
            return f"KafkaRequest: topic_key={self.topic_key} kafka_key={self.kafka_key}"
        elif self.topic is not None:
            return f"KafkaRequest: topic={self.topic} kafka_key={self.kafka_key}"
        else:
            return f"KafkaRequest: kafka_key={self.kafka_key}"

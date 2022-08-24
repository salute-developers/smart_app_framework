from typing import Dict

from core.configs.global_constants import CALLBACK_ID_HEADER, KAFKA_REPLY_TOPIC
from core.request.kafka_request import KafkaRequest


class SmartKitKafkaRequest(KafkaRequest):
    KAFKA_REPLY_TOPIC = KAFKA_REPLY_TOPIC
    KAFKA_EXTRA_HEADERS = "kafka_extraHeaders"

    def __init__(self, items, id=None):
        super(SmartKitKafkaRequest, self).__init__(items)
        items = items or {}
        self._callback_id = items.get(self._callback_id_header_name)
        self._kafka_replyTopic = items.get(self.KAFKA_REPLY_TOPIC)
        self._kafka_extraHeaders = items.get(self.KAFKA_EXTRA_HEADERS) or {}

    @property
    def _callback_id_header_name(self):
        return CALLBACK_ID_HEADER

    def _get_new_headers(self, source_mq_message):
        headers_dict = dict(super(SmartKitKafkaRequest, self)._get_new_headers(source_mq_message))
        if self._callback_id:
            headers_dict[self._callback_id_header_name] = str(self._callback_id).encode()
        if self._kafka_replyTopic:
            headers_dict[self.KAFKA_REPLY_TOPIC] = str(self._kafka_replyTopic).encode()
        if self._kafka_extraHeaders:
            for k, v in self._kafka_extraHeaders.items():
                headers_dict[k] = str(v).encode()
        headers_list = list(headers_dict.items())
        return headers_list

    def __str__(self):
        return f"KafkaRequest: kafka_key={self.kafka_key}"

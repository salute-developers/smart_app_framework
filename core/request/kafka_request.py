from __future__ import annotations

from typing import TYPE_CHECKING

from core.request.base_request import BaseRequest
from core.logging.logger_utils import log
import core.logging.logger_constants as log_const

if TYPE_CHECKING:
    from core.mq.kafka.kafka_publisher import KafkaPublisher
    from aiokafka import ConsumerRecord
    from typing import Dict, Optional, Sequence, Tuple, Any


class KafkaRequest(BaseRequest):
    TOPIC_KEY = "topic_key"
    KAFKA_KEY = "kafka_key"
    TOPIC = "topic"

    def __init__(self, items: Dict[str, str], id=None):
        super().__init__(items)
        items = items or {}
        self.topic_key = items.get(self.TOPIC_KEY)
        self.kafka_key = items.get(self.KAFKA_KEY)
        # topic_key has priority over topic
        self.topic = items.get(self.TOPIC)

    def update_empty_items(self, items: Dict[str, str]) -> None:
        self.topic_key = self.topic_key or items.get(self.TOPIC_KEY)
        self.kafka_key = self.kafka_key or items.get(self.KAFKA_KEY)
        self.topic = self.topic or items.get(self.TOPIC)

    @property
    def group_key(self) -> Optional[str]:
        return "{}_{}".format(self.kafka_key, self.topic_key) if (self.topic_key and self.kafka_key) else None

    def _get_new_headers(self, source_mq_message: ConsumerRecord) -> Sequence[Tuple[str, bytes]]:
        headers = source_mq_message.headers or []
        return headers

    async def send(self, data: bytes, publisher: KafkaPublisher, source_mq_message: ConsumerRecord) -> None:
        headers = self._get_new_headers(source_mq_message)
        if self.topic is not None:
            await publisher.send_to_topic(data, source_mq_message.key, self.topic, headers=headers)
        elif self.topic_key is not None:
            await publisher.send(data, source_mq_message.key, self.topic_key, headers=headers)
        else:
            log_params = {
                "data": str(data),
                log_const.KEY_NAME: log_const.EXCEPTION_VALUE
            }
            log("KafkaRequest: got no topic and no topic_key", params=log_params, level="ERROR")

    async def run(self, data: bytes, params: Dict[str, Any]) -> None:
        publishers = params["publishers"]
        publisher = publishers[self.kafka_key]
        await self.send(data=data, publisher=publisher, source_mq_message=params["mq_message"])

    def __str__(self) -> str:
        if self.topic_key is not None:
            return f"KafkaRequest: topic_key={self.topic_key} kafka_key={self.kafka_key}"
        elif self.topic is not None:
            return f"KafkaRequest: topic={self.topic} kafka_key={self.kafka_key}"
        else:
            return f"KafkaRequest: kafka_key={self.kafka_key}"

from __future__ import annotations

from typing import TYPE_CHECKING

from aiokafka.abc import ConsumerRebalanceListener

if TYPE_CHECKING:
    from typing import List, Callable
    from kafka import TopicPartition
    from aiokafka import AIOKafkaConsumer


class CoreConsumerRebalanceListener(ConsumerRebalanceListener):
    def __init__(self, consumer: AIOKafkaConsumer,
                 on_assign_callback: Callable[[AIOKafkaConsumer, List[TopicPartition]], None]):
        self._consumer = consumer
        self._on_assign_callback = on_assign_callback

    def on_partitions_assigned(self, assigned: List[TopicPartition]):
        self._on_assign_callback(self._consumer, assigned)

    def on_partitions_revoked(self, revoked):
        pass

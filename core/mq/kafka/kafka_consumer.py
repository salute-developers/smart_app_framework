# coding: utf-8
from __future__ import annotations

import logging
import os
import time
import uuid
from typing import TYPE_CHECKING

from aiokafka import AIOKafkaConsumer, TopicPartition
from kafka.errors import KafkaError

import core.logging.logger_constants as log_const
from core.logging.logger_utils import log
from core.monitoring.monitoring import monitoring
from core.mq.kafka.base_kafka_consumer import BaseKafkaConsumer
from core.mq.kafka.consumer_rebalance_listener import CoreConsumerRebalanceListener

if TYPE_CHECKING:
    from aiokafka import ConsumerRecord
    from typing import Optional, Callable, Iterable, AsyncGenerator, Any, Dict, List
    from asyncio import AbstractEventLoop


class KafkaConsumer(BaseKafkaConsumer):
    def __init__(self, config: Dict[str, Any], loop: AbstractEventLoop):
        self._config = config["consumer"]
        self.assign_offset_end = self._config.get("assign_offset_end", False)
        conf = self._config["conf"]
        self._update_old_config(conf)
        conf.setdefault("group_id", str(uuid.uuid1()))
        self.autocommit_enabled = conf.get("enable_auto_commit", True)
        internal_log_path = self._config.get("internal_log_path")
        if internal_log_path:
            debug_logger = logging.getLogger("debug_consumer")  # TODO add debug logger to _consumer events
            timestamp = time.strftime("_%d%m%Y_")
            debug_logger.addHandler(logging.FileHandler(
                "{}/kafka_consumer_debug{}{}.log".format(internal_log_path, timestamp, os.getpid())
            ))
        self._consumer = AIOKafkaConsumer(**conf, loop=loop)
        loop.run_until_complete(self._consumer.start())

    def on_assign_offset_end(self, consumer: AIOKafkaConsumer, partitions: List[TopicPartition]) -> None:
        for p in partitions:
            p.offset = consumer.last_stable_offset(p)
        self.on_assign_log(consumer, partitions)
        try:
            consumer.assign(partitions)
        except KafkaError as e:
            self._error_callback(e)

    def on_coop_assign_offset_end(self, consumer: AIOKafkaConsumer, partitions: List[TopicPartition]) -> None:
        for p in partitions:
            p.offset = consumer.last_stable_offset(p)
        self.on_assign_log(consumer, partitions)
        consumer.assign(consumer.assignment().update(partitions))

    def on_assign_log(self, consumer: AIOKafkaConsumer, partitions: List[TopicPartition]) -> None:
        log_level = "WARNING"
        params = {
            "partitions": str(list([str(partition) for partition in partitions or []])),
            log_const.KEY_NAME: log_const.KAFKA_ON_ASSIGN_VALUE,
            "log_level": log_level
        }
        log("KafkaConsumer.subscribe<on_assign>: assign %(partitions)s %(log_level)s", params=params, level=log_level)

    def subscribe(self, topics: Iterable[str] = None) -> None:
        topics = list(set(topics or list(self._config["topics"].values())))

        params = {
            "topics": topics
        }
        log("Topics to subscribe: %(topics)s", params=params)

        try:
            self._consumer.subscribe(topics)
        except KafkaError as e:
            self._error_callback(e)

    def get_on_assign_callback(self) -> Callable[[AIOKafkaConsumer, List[TopicPartition]], None]:
        if "cooperative" in self._config["conf"].get("partition_assignment_strategy", ""):
            callback = self.on_coop_assign_offset_end
        else:
            callback = self.on_assign_offset_end
        return callback

    def unsubscribe(self) -> None:
        self._consumer.unsubscribe()

    async def poll(self) -> Optional[ConsumerRecord]:
        msg = await self._consumer.getone()
        return self._process_message(msg)

    async def consume(self, num_messages: int = 1) -> AsyncGenerator[Optional[ConsumerRecord], None]:
        timeout_ms = self._config["poll_timeout"] * 1000
        messages = await self._consumer.getmany(max_records=num_messages, timeout_ms=timeout_ms)
        for partition_messages in messages.values():
            for msg in partition_messages:
                processed = self._process_message(msg)
                yield processed

    async def commit_offset(self, msg: ConsumerRecord) -> None:
        if msg is not None:
            if not self.autocommit_enabled:
                tp = TopicPartition(msg.topic, msg.partition)
                try:
                    await self._consumer.commit({tp: msg.offset + 1})
                except KafkaError as e:
                    self._error_callback(e)

    def get_msg_create_time(self, mq_message: ConsumerRecord) -> int:
        timestamp = mq_message.timestamp
        return timestamp

    def _error_callback(self, err: Any) -> None:
        params = {
            "error": str(err),
            log_const.KEY_NAME: log_const.EXCEPTION_VALUE
        }
        log("KafkaConsumer: Error: %(error)s", params=params, level="WARNING")
        monitoring.got_counter("kafka_consumer_exception")

    # noinspection PyMethodMayBeStatic
    def _process_message(self, msg: ConsumerRecord) -> Optional[ConsumerRecord]:
        if msg.value:
            if msg.headers is None:
                msg.headers = list()
            return msg

    async def close(self) -> None:
        await self._consumer.stop()
        log(f"consumer to topics {self._config['topics']} closed.")

    def _update_old_config(self, conf: Dict[str, Any]) -> None:
        if "default.topic.config" in conf:
            conf.update(conf["default.topic.config"])
            del conf["default.topic.config"]
        param_old_to_new = {
            "group.id": "group_id",
            "enable.auto.commit": "enable_auto_commit",
            "partition.assignment.strategy": "partition_assignment_strategy",
            "bootstrap.servers": "bootstrap_servers",
            "topic.metadata.refresh.interval.ms": "metadata_max_age_ms",
            "session.timeout.ms": "session_timeout_ms",
            "auto.commit.interval.ms": "auto_commit_interval_ms",
            "enable.auto.offset.store": None,
            "auto.offset.reset": "auto_offset_reset",
            "debug": None,
            "security.protocol": "security_protocol"
        }  # TODO map other old configs as well
        for old, new in param_old_to_new.items():
            if old in conf:
                if new:
                    conf[new] = conf[old]
                del conf[old]

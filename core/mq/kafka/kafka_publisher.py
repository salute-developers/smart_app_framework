# coding: utf-8
from __future__ import annotations

import logging
import os
import time
from typing import TYPE_CHECKING

from aiokafka import AIOKafkaProducer
from aiokafka.errors import KafkaTimeoutError
from aiokafka.helpers import create_ssl_context

import core.logging.logger_constants as log_const
from core.logging.logger_utils import log
from core.monitoring.monitoring import monitoring
from core.mq.kafka.base_kafka_publisher import BaseKafkaPublisher

if TYPE_CHECKING:
    from asyncio import AbstractEventLoop
    from typing import Optional, Tuple, Any, Dict, Sequence


class KafkaPublisher(BaseKafkaPublisher):
    def __init__(self, config: Dict[str, Any], loop: AbstractEventLoop):
        self._config = config["publisher"]
        conf = self._config["conf"]
        self._update_old_config(conf)
        self._setup_ssl(conf, self._config.get("ssl"))
        internal_log_path = self._config.get("internal_log_path")
        if internal_log_path:
            debug_logger = logging.getLogger("debug_publisher")  # TODO add debug logger to _publisher events
            timestamp = time.strftime("_%d%m%Y_")
            debug_logger.addHandler(logging.FileHandler(
                "{}/kafka_publisher_debug{}{}.log".format(internal_log_path, timestamp, os.getpid())
            ))
        self._producer = AIOKafkaProducer(**conf, loop=loop)
        loop.run_until_complete(self._producer.start())

    async def send(self, value: bytes, key: Any = None, topic_key: Optional[str] = None,
                   headers: Optional[Sequence[Tuple[str, bytes]]] = None) -> None:
        topic = self._config["topic"]
        if topic_key is not None:
            topic = topic[topic_key]
        print("topic:", topic)
        await self._producer.send_and_wait(topic=topic, value=value, headers=headers or list(), key=key)

    async def send_to_topic(self, value: bytes, key: Any = None, topic: Optional[str] = None,
                            headers: Optional[Sequence[Tuple[str, bytes]]] = None) -> None:
        if topic is None:
            params = {
                "message": str(value),
                log_const.KEY_NAME: log_const.EXCEPTION_VALUE
            }
            log("KafkaProducer: Failed sending message %{message}s. Topic is not defined", params=params,
                level="ERROR")
        try:
            await self._producer.send_and_wait(topic=topic, value=value, headers=headers or list(), key=key)
            self._delivery_callback(None, value)
        except KafkaTimeoutError as e:
            self._error_callback(e)
            self._delivery_callback(e, value)
            raise e

    def _error_callback(self, err: Any) -> None:
        params = {
            "error": str(err),
            log_const.KEY_NAME: log_const.EXCEPTION_VALUE
        }
        log("KafkaProducer: Error: %(error)s", params=params, level="ERROR")
        monitoring.got_counter("kafka_producer_exception")

    def _delivery_callback(self, err: Any, msg_value: bytes) -> None:
        if err:
            try:
                msg_value = msg_value.decode()
                log("KafkaProducer: Message %(message)s send failed: %(error)s",
                    params={
                        "message": str(msg_value),
                        "error": str(err),
                        log_const.KEY_NAME: log_const.EXCEPTION_VALUE},
                    level="ERROR")
            except UnicodeDecodeError:
                log("KafkaProducer: %(text)s: %(error)s",
                    params={"text": f"Can't decode: {str(msg_value)}",
                            "error": err,
                            log_const.KEY_NAME: log_const.EXCEPTION_VALUE},
                    level="ERROR",
                    exc_info=True)
            monitoring.got_counter("kafka_producer_exception")

    async def close(self) -> None:
        await self._producer.stop()

    def _setup_ssl(self, conf: Dict[str, Any], ssl_config: Optional[Dict[str, Any]] = None) -> None:
        if ssl_config:
            context = create_ssl_context(**ssl_config)
            conf["security_protocol"] = "SSL"
            conf["ssl_context"] = context

    def _update_old_config(self, conf: Dict[str, Any]) -> None:
        if "ssl.ca.location" in conf:
            context = create_ssl_context(
                cafile=conf["ssl.ca.location"],
                certfile=conf["ssl.certificate.location"],
                keyfile=conf["ssl.key.location"]
            )
            conf["security_protocol"] = "SSL"
            conf["ssl_context"] = context
            del conf["ssl.ca.location"]
            del conf["ssl.certificate.location"]
            del conf["ssl.key.location"]
        param_old_to_new = {
            "bootstrap.servers": "bootstrap_servers",
            "topic.metadata.refresh.interval.ms": "metadata_max_age_ms",
            "security.protocol": "security_protocol"
        }
        for old, new in param_old_to_new.items():
            if old in conf:
                if new:
                    conf[new] = conf[old]
                del conf[old]

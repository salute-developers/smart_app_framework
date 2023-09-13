import asyncio
import cProfile
import concurrent.futures
import gc
import hashlib
import json
import pstats
import signal
import time
import tracemalloc
from collections import namedtuple
from functools import lru_cache, cached_property
from typing import Union, Dict

from confluent_kafka.cimpl import KafkaException, Message as KafkaMessage

import scenarios.logging.logger_constants as log_const
from core.basic_models.actions.command import Command
from core.configs.global_constants import KAFKA_REPLY_TOPIC
from core.logging.logger_utils import log, UID_STR, MESSAGE_ID_STR
from core.message.from_message import SmartAppFromMessage
from core.model.base_user import BaseUser
from core.model.heapq.heapq_storage import HeapqKV
from core.monitoring.monitoring import monitoring
from core.mq.kafka.async_kafka_publisher import AsyncKafkaPublisher
from core.mq.kafka.kafka_consumer import KafkaConsumer
from core.utils.memstats import get_top_malloc
from core.utils.pickle_copy import pickle_deepcopy
from core.utils.stats_timer import StatsTimer
from smart_kit.compatibility.commands import combine_commands
from smart_kit.message.get_to_message import get_to_message
from smart_kit.message.smartapp_to_message import SmartAppToMessage
from smart_kit.names import message_names
from smart_kit.names.message_names import ANSWER_TO_USER, RUN_APP, MESSAGE_TO_SKILL, SERVER_ACTION, CLOSE_APP
from smart_kit.request.kafka_request import SmartKitKafkaRequest
from smart_kit.start_points.base_main_loop import BaseMainLoop
from smart_kit.start_points.constants import WORKER_EXCEPTION, POD_UP


def _enrich_config_from_secret(kafka_config, secret_config):
    for key in kafka_config:
        if secret_config.get(key):
            kafka_config[key]["consumer"]["conf"].update(secret_config[key]["consumer"]["conf"])
            kafka_config[key]["publisher"]["conf"].update(secret_config[key]["publisher"]["conf"])
    return kafka_config


class MainLoop(BaseMainLoop):
    # in milliseconds. log event if elapsed time more than value
    MAX_LOG_TIME = 60
    BAD_ANSWER_COMMAND = Command(message_names.ERROR, {"code": -1, "description": "Invalid Answer Message"})

    def __init__(self, *args, **kwargs):
        log("%(class_name)s.__init__ started.", params={log_const.KEY_NAME: log_const.STARTUP_VALUE,
                                                        "class_name": self.__class__.__name__})
        self.loop = asyncio.get_event_loop()
        self.health_check_server_future = None
        super().__init__(*args, **kwargs)
        # We have many async loops for messages processing in main thread
        # And 1 thread for independent consecutive Kafka reading
        self.kafka_executor_pool = concurrent.futures.ThreadPoolExecutor(max_workers=1)
        self._timers = dict()  # stores aio timers for callbacks
        self.template_settings = self.settings["template_settings"]
        self.profiling_settings = self.template_settings.get("profiling", {})
        self.profile_cpu = self.profiling_settings.get("cpu", False)
        self.profile_cpu_path = self.profiling_settings.get("cpu_path", "/tmp/dp.cpu.prof")
        self.profile_memory = self.profiling_settings.get("memory", False)
        self.profile_memory_log_delta = self.profiling_settings.get("memory_log_delta", 30)
        self.profile_memory_depth = self.profiling_settings.get("memory_depth", 4)
        self.behavior_timers_tear_down_delay = self.template_settings.get("behavior_timers_tear_down_delay", 15)
        self.no_kafka_messages_poll_time = self.template_settings.get("no_kafka_messages_poll_time", 0.01)
        self.waiting_message_timeout = self.settings["template_settings"].get("waiting_message_timeout", {})
        self.kafka_broker_settings = self.settings["template_settings"].get("route_kafka_broker") or []
        self.warning_delay = self.waiting_message_timeout.get('warning', 200)
        self.skip_delay = self.waiting_message_timeout.get('skip', 8000)
        self.worker_tasks = []
        self.max_concurrent_messages = self.template_settings.get("max_concurrent_messages", 10)
        self.queues = [asyncio.Queue() for _ in range(self.max_concurrent_messages)]
        self.total_messages = 0

        # override default value
        self.MAX_LOG_TIME = self._get_max_log_time_from_settings(settings=self.template_settings or {})

        try:
            kafka_config = _enrich_config_from_secret(
                self.settings["kafka"]["template-engine"], self.settings.get("secret_kafka", {})
            )

            consumers = {}
            publishers = {}
            log("%(class_name)s START CONSUMERS/PUBLISHERS CREATE",
                params={"class_name": self.__class__.__name__}, level="WARNING")
            kafka_config_copy = pickle_deepcopy(kafka_config)
            for key, config in kafka_config_copy.items():
                if config.get("consumer"):
                    consumers.update({key: KafkaConsumer(config)})
                if config.get("publisher"):
                    publishers.update({key: AsyncKafkaPublisher(config)})
            log(
                "%(class_name)s FINISHED CONSUMERS/PUBLISHERS CREATE",
                params={"class_name": self.__class__.__name__}, level="WARNING"
            )

            self.app_name = self.settings.app_name
            self.consumers = consumers
            for key in self.consumers:
                self.consumers[key].subscribe()
            self.publishers = publishers
            self.behaviors_timeouts_value_cls = namedtuple('behaviors_timeouts_value',
                                                           'db_uid, callback_id, mq_message, kafka_key')
            self.behaviors_timeouts = HeapqKV(value_to_key_func=lambda val: val.callback_id)
            self.concurrent_messages = 0

            log("%(class_name)s.__init__ completed.", params={log_const.KEY_NAME: log_const.STARTUP_VALUE,
                                                              "class_name": self.__class__.__name__})
        except Exception:
            log("%(class_name)s.__init__ exception.", params={log_const.KEY_NAME: log_const.STARTUP_VALUE,
                                                              "class_name": self.__class__.__name__},
                level="ERROR", exc_info=True)
            raise

    def _get_max_log_time_from_settings(self, settings: dict) -> int:
        """Get max log time from settings or use default value for kafka polling"""
        return settings.get("kafka_max_log_time", self.MAX_LOG_TIME)

    def run(self):
        signal.signal(signal.SIGINT, self.stop)
        signal.signal(signal.SIGTERM, self.stop)
        log("%(class_name)s.run started", params={log_const.KEY_NAME: log_const.STARTUP_VALUE,
                                                  "class_name": self.__class__.__name__})
        monitoring.pod_event(self.app_name, POD_UP)
        loop = asyncio.get_event_loop()
        loop.run_until_complete(self.general_coro())

        log("%(class_name)s stopping kafka", level="WARNING", params={"class_name": self.__class__.__name__})

        for kafka_key in self.consumers:
            self.consumers[kafka_key].close()
        for kafka_key in self.publishers:
            self.publishers[kafka_key].close()
        log("%(class_name)s EXIT.", level="WARNING", params={"class_name": self.__class__.__name__})

    async def general_coro(self):
        tasks = [self.process_consumer(kafka_key) for kafka_key in self.consumers]
        if self.health_check_server is not None:
            tasks.append(self.healthcheck_coro())
        await asyncio.gather(*tasks)

    async def healthcheck_coro(self):
        while self.is_work:
            if (
                    not self.health_check_server_future or
                    self.health_check_server_future.done() or
                    self.health_check_server_future.cancelled()
            ):
                self.health_check_server_future = self.loop.run_in_executor(None, self.health_check_server.iterate)
            await asyncio.sleep(0.5)
        log("healthcheck_coro stopped")

    async def process_consumer(self, kafka_key):
        start_time = self.loop.time()
        if self.profile_cpu:
            cpu_pr = cProfile.Profile()
            cpu_pr.enable()
        else:
            cpu_pr = None
        if self.profile_memory:
            tracemalloc.start(self.profile_memory_depth)

        log(f"Starting %(class_name)s in {self.max_concurrent_messages} coro",
            params={"class_name": self.__class__.__name__})

        for i, queue in enumerate(self.queues):
            task = asyncio.create_task(self.queue_worker(f'worker-{i}', queue))
            self.worker_tasks.append(task)

        await self.poll_kafka(kafka_key, self.queues)  # blocks while self.is_works

        log("waiting for process unfinished tasks in queues")
        await asyncio.gather(*(queue.join() for queue in self.queues))

        time_delta = self.loop.time() - start_time
        log(f"Process Consumer exit: {self.total_messages} msg in {int(time_delta)} sec", level="DEBUG")

        t = self.loop.time()
        log(f"wait timers to do their jobs for {self.behavior_timers_tear_down_delay} secs...")
        while self._timers and (self.loop.time() - t) < self.behavior_timers_tear_down_delay:
            await asyncio.sleep(1)

        for task in self.worker_tasks:
            cancell_status = task.cancel()
            log(f"{task} cancell status: {cancell_status} ")

        log(f"Stop consuming messages. All workers closed, erasing {len(self._timers)} timers.")

        if self.profile_memory:
            log(f"{get_top_malloc(trace_limit=16)}")
            tracemalloc.stop()
        if cpu_pr is not None:
            cpu_pr.disable()
            stats = pstats.Stats(cpu_pr)
            stats.sort_stats(pstats.SortKey.TIME)
            stats.print_stats(10)
            stats.dump_stats(filename=self.profile_cpu_path)

    async def queue_worker(self, worker_id, queue):
        message_value = None
        last_poll_begin_time = self.loop.time()
        last_mem_log = self.loop.time()
        log(f"-- Starting {worker_id} iter", params={log_const.KEY_NAME: "starting"})

        while self.is_work:
            if self.profile_memory and worker_id == 0 and \
                    self.loop.time() - last_mem_log > self.profile_memory_log_delta:
                top = get_top_malloc(trace_limit=0)
                async_counts = len(self.loop._ready), len(self.loop._scheduled), len(self.loop._asyncgens)
                async_values = " + ".join(map(str, async_counts))
                log(
                    f"Total memory: {top}; "
                    f"Async: {async_values} = {sum(async_counts)}; "
                    f"Trash: {gc.get_count()} ",
                    level="DEBUG"
                )
                last_mem_log = self.loop.time()

            worker_from_last_message_ms = int((self.loop.time() - last_poll_begin_time) * 1000)
            stats = f"From last message coro {worker_id} time: {worker_from_last_message_ms} msecs\n"
            log_params = {
                log_const.KEY_NAME: "timings",
                "worker_from_last_message_ms": worker_from_last_message_ms,
                "worker_id": worker_id
            }
            last_poll_begin_time = self.loop.time()
            handle_executable, kwargs = await queue.get()
            kafka_key, mq_message = kwargs.get("kafka_key"), kwargs.get("mq_message")
            worker_kwargs = {"worker_id": worker_id,
                             "stats": stats,
                             "log_params": log_params,
                             }

            self.total_messages += 1
            try:
                await handle_executable(kwargs, worker_kwargs)

            except KafkaException as kafka_exp:
                log("kafka error: %(kafka_exp)s.",
                    params={log_const.KEY_NAME: log_const.STARTUP_VALUE,
                            "kafka_exp": str(kafka_exp),
                            log_const.REQUEST_VALUE: str(message_value)},
                    level="ERROR", exc_info=True)

            except Exception:
                monitoring.pod_event(self.app_name, WORKER_EXCEPTION)
                log("%(class_name)s worker error. Kafka key %(kafka_key)s",
                    params={log_const.KEY_NAME: "worker_exception",
                            "kafka_key": kafka_key,
                            log_const.REQUEST_VALUE: str(message_value)},
                    level="ERROR", exc_info=True)
                try:
                    consumer = self.consumers[kafka_key]
                    consumer.commit_offset(mq_message)
                except Exception:
                    log("Error handling worker fail exception.", level="ERROR", exc_info=True)
                    raise
            finally:
                queue.task_done()

        log(f"-- Stop worker {worker_id}")

    async def poll_kafka(self, kafka_key, queues):
        consumer = self.consumers[kafka_key]
        log_params = {log_const.KEY_NAME: "timings_polling"}
        while self.is_work:
            with StatsTimer() as poll_timer:
                # Max delay between polls configured in consumer.poll_timeout param
                mq_message = consumer.poll()
            log_params["kafka_polling"] = poll_timer.msecs
            if poll_timer.msecs > self.MAX_LOG_TIME:
                log("Long poll time: %(kafka_polling)s msecs\n", params=log_params, level="WARNING")
            if mq_message:
                kwargs = {"kafka_key": kafka_key,
                          "mq_message": mq_message}
                not_empty_queues_count = await self.put_to_queue(mq_message, self.do_incoming_handling, kwargs)
                log(f"Poll time: %(kafka_polling)s msecs\n, not_empty_queues count: {not_empty_queues_count}.",
                    params=log_params, level="INFO")
            else:
                await asyncio.sleep(self.no_kafka_messages_poll_time)  # callbacks can work here

        log("Stop poll_kafka consumer.")

    async def put_to_queue(self, mq_message, executable, kwargs):
        key = mq_message.key()
        if key:
            queue_index = int(hashlib.sha1(key).hexdigest(), 16) % (len(self.queues) - 1)
        else:
            queue_index = (len(self.queues) - 1)

        self.queues[queue_index].put_nowait((executable, kwargs))
        not_empty_cnt = sum(1 for queue in self.queues if not queue.empty())
        for _ in range(not_empty_cnt):
            await asyncio.sleep(0)
        return not_empty_cnt

    async def do_incoming_handling(self, kwargs, worker_kwargs):
        mq_message, kafka_key = kwargs.get("mq_message"), kwargs.get("kafka_key")
        stats = worker_kwargs.get("stats")
        worker_id = worker_kwargs.get("worker_id")
        consumer = self.consumers[kafka_key]

        if mq_message:
            self.concurrent_messages += 1
            print(f"-- Processing {self.concurrent_messages} msgs at {worker_id} iter")

            headers = mq_message.headers()
            if headers is None:
                self.concurrent_messages -= 1
                raise Exception("No incoming message headers found.")

            try:
                await self.process_message(mq_message, consumer, kafka_key, stats)
            finally:
                self.concurrent_messages -= 1

    def _generate_answers(self, user, commands, message, **kwargs):
        topic_key = kwargs["topic_key"]
        kafka_key = kwargs["kafka_key"]
        answers = []
        commands = commands or []

        commands = combine_commands(commands, user)

        for command in commands:
            request = SmartKitKafkaRequest(id=None, items=command.request_data)
            request.update_empty_items({
                "kafka_key": kafka_key,
                "topic_key": topic_key,
                "topic": user.local_vars.get(KAFKA_REPLY_TOPIC) if command.name == ANSWER_TO_USER else None
            })

            to_message = get_to_message(command.name)
            answer = to_message(command=command, message=message, request=request,
                                masking_fields=self.masking_fields,
                                validators=self.to_msg_validators)
            if answer.validate():
                answers.append(answer)
            else:
                answers.append(SmartAppToMessage(self.BAD_ANSWER_COMMAND, message=message, request=request))

            monitoring.counter_outgoing(self.app_name, command.name, answer, user)

        return answers

    def _get_timeout_from_message(self, orig_message_raw: Dict, callback_id, headers):
        timeout_from_message = SmartAppFromMessage(orig_message_raw, headers=headers,
                                                   masking_fields=self.masking_fields,
                                                   validators=self.from_msg_validators)
        timeout_from_message.callback_id = callback_id
        return timeout_from_message

    def _get_topic_key(self, mq_message: KafkaMessage, kafka_key):
        topic_names_2_key = self._topic_names_2_key(kafka_key)
        return self.default_topic_key(kafka_key) or topic_names_2_key[mq_message.topic()]

    def _is_message_timeout_to_skip(self, message: SmartAppFromMessage, waiting_message_time: int):
        # Returns True if timeout is found
        waiting_message_timeout = self.template_settings.get("waiting_message_timeout", {})
        warning_delay = waiting_message_timeout.get("warning", 200)
        skip_delay = waiting_message_timeout.get("skip", 8000)
        log_level = None
        make_break = False

        if waiting_message_time >= skip_delay:
            # Too old message
            log_level = "ERROR"
            monitoring.counter_mq_skip_waiting(self.app_name)
            make_break = True

        elif waiting_message_time >= warning_delay:
            # Warn, but continue message processing
            log_level = "WARNING"
            monitoring.counter_mq_long_waiting(self.app_name)

        if log_level is not None:
            log("Out of time message %(waiting_message_time)s msecs, "
                "mid: %(mid)s ",
                params={
                    log_const.KEY_NAME: "waiting_message_timeout",
                    "waiting_message_time": waiting_message_time,
                    "mid": message.incremental_id,
                    log_const.REQUEST_VALUE: message.as_str,
                },
                level=log_level)
        return make_break

    async def process_message(self, mq_message: KafkaMessage, consumer, kafka_key, stats):
        topic_key = self._get_topic_key(mq_message, kafka_key)

        save_tries = 0
        user_save_no_collisions = False
        skip_message = False
        user = None
        db_uid = None
        message = None
        while save_tries < self.user_save_collisions_tries and not user_save_no_collisions:
            save_tries += 1
            message_value = json.loads(mq_message.value())
            message = SmartAppFromMessage(message_value,
                                          headers=mq_message.headers(),
                                          masking_fields=self.masking_fields,
                                          creation_time=consumer.get_msg_create_time(mq_message))

            if message.validate():
                waiting_message_time = 0
                if message.creation_time:
                    waiting_message_time = time.time() * 1000 - message.creation_time
                    stats += "Waiting message: {} msecs\n".format(waiting_message_time)

                stats += "Mid: {}\n".format(message.incremental_id)
                monitoring.sampling_mq_waiting_time(self.app_name, waiting_message_time / 1000)

                if self._is_message_timeout_to_skip(message, waiting_message_time):
                    skip_message = True
                    break

                db_uid = message.db_uid
                with StatsTimer() as load_timer:
                    user = await self.load_user(db_uid, message)
                monitoring.sampling_load_time(self.app_name, load_timer.secs)
                stats += "Loading time: {} msecs\n".format(load_timer.msecs)

                # check_message_key
                message_key = self._get_str_message_key(mq_message.key(), incremental_id=message.incremental_id,
                                                        uid=message.uid, user=user)
                valid_key = self._get_valid_message_key(message)
                if message_key != valid_key:
                    log(f"Failed to check Kafka message %(message_name)s key {message_key} != {valid_key}",
                        params={
                            log_const.KEY_NAME: "check_kafka_key_validation",
                            MESSAGE_ID_STR: message.incremental_id,
                            UID_STR: message.uid,
                            "kafka_key": kafka_key,
                            "message_key": message_key,
                            "message_name": message.type,
                        }, user=user,
                        level="WARNING")
                    if self.settings["template_settings"].get("wrong_key_resend", True):
                        dest_topic = mq_message.topic()
                        self.publishers[kafka_key].send_to_topic(mq_message.value(), valid_key, dest_topic,
                                                                 mq_message.headers())
                        skip_message = True
                        log("Kafka message %(message_name)s with invalid Kafka message key %(message_key)s "
                            f"resend again with a valid key: '{valid_key}' to '{dest_topic}'",
                            params={
                                log_const.KEY_NAME: "kafka_message_key_recovery",
                                MESSAGE_ID_STR: message.incremental_id,
                                UID_STR: message.uid,
                                "kafka_key": kafka_key,
                                "message_key": message_key,
                                "message_name": message.type,
                            }, user=user,
                            level=self.settings["template_settings"].get("kafka_message_key_recovery_log_level",
                                                                         "DEBUG"))
                        break
                else:
                    log("INCOMING FROM TOPIC: %(topic)s partition %(message_partition)s HEADERS: %(headers)s DATA: "
                        "%(incoming_data)s",
                        params={log_const.KEY_NAME: "incoming_message",
                                "topic": mq_message.topic(),
                                "message_partition": mq_message.partition(),
                                "message_key": (mq_message.key() or b"").decode('utf-8', 'backslashreplace'),
                                "message_id": message.incremental_id,
                                "kafka_key": kafka_key,
                                "incoming_data": str(message.masked_value),
                                "length": len(message.as_str),
                                "headers": mq_message.headers(),
                                "waiting_message": waiting_message_time,
                                "surface": message.device.surface,
                                MESSAGE_ID_STR: message.incremental_id},
                        user=user)

                    if KAFKA_REPLY_TOPIC in message.headers and \
                            message.message_name in [RUN_APP, MESSAGE_TO_SKILL, SERVER_ACTION, CLOSE_APP]:
                        if user.local_vars.get(KAFKA_REPLY_TOPIC):
                            log("MainLoop.iterate: kafka_replyTopic collision(got saved in local_vars)",
                                params={log_const.KEY_NAME: "ignite_collision",
                                        "db_uid": db_uid,
                                        "message_key": mq_message.key(),
                                        "message_partition": mq_message.partition(),
                                        "kafka_key": kafka_key,
                                        "uid": user.id,
                                        "saved_topic": user.local_vars.get(KAFKA_REPLY_TOPIC),
                                        "current_topic": message.headers[KAFKA_REPLY_TOPIC]},
                                user=user, level="WARNING")
                        user.local_vars.set(KAFKA_REPLY_TOPIC, message.headers[KAFKA_REPLY_TOPIC])

                    publish_time_ms_sum = 0
                    with StatsTimer() as script_timer:
                        async for command in self.model.answer(message, user):
                            answers = self._generate_answers(user=user, commands=[command], message=message,
                                                             topic_key=topic_key, kafka_key=kafka_key)
                            if answers:
                                for answer in answers:
                                    with StatsTimer() as publish_timer:
                                        self._send_request(user, answer, mq_message)
                                    publish_time_ms_sum += publish_timer.msecs
                                    stats += "Publishing time: {} msecs\n".format(publish_timer.msecs)

                    script_time_ms = script_timer.msecs - publish_time_ms_sum
                    script_time_sec = script_time_ms / 1000
                    monitoring.sampling_script_time(self.app_name, script_time_sec)
                    stats += "Script time: {} msecs\n".format(script_time_ms)

                    with StatsTimer() as save_timer:
                        user_save_no_collisions = await self.save_user(db_uid, user, message)

                    monitoring.sampling_save_time(self.app_name, save_timer.secs)
                    stats += "Saving time: {} msecs\n".format(save_timer.msecs)

                    log(stats, user=user)

                    if user_save_no_collisions:
                        self.save_behavior_timeouts(user, mq_message, kafka_key)
                    else:
                        log("MainLoop.iterate: save user got collision on uid %(uid)s db_version %(db_version)s.",
                            user=user,
                            params={log_const.KEY_NAME: "ignite_collision",
                                    "db_uid": db_uid,
                                    "message_key": mq_message.key(),
                                    "message_partition": mq_message.partition(),
                                    "kafka_key": kafka_key,
                                    "uid": user.id,
                                    "db_version": str(user.private_vars.get(user.USER_DB_VERSION))},
                            level="WARNING")
                        continue
            else:
                try:
                    data = message.masked_value
                except Exception:
                    data = "<DATA FORMAT ERROR>"
                log("Message validation failed, skip message handling.",
                    params={log_const.KEY_NAME: "invalid_message",
                            "data": data,
                            "message_key": (mq_message.key() or b"").decode('utf-8', 'backslashreplace')},
                    level="ERROR")
                monitoring.counter_invalid_message(self.app_name)
                break
        if user and not user_save_no_collisions and not skip_message:
            log("MainLoop.iterate: db_save collision all tries left on uid %(uid)s db_version %(db_version)s.",
                user=user,
                params={log_const.KEY_NAME: "ignite_collision",
                        "db_uid": db_uid,
                        "message_key": mq_message.key(),
                        "message_partition": mq_message.partition(),
                        "kafka_key": kafka_key,
                        "uid": user.id,
                        "db_version": str(user.private_vars.get(user.USER_DB_VERSION))},
                level="WARNING")
            await self.postprocessor.postprocess(user, message)
            monitoring.counter_save_collision_tries_left(self.app_name)
        consumer.commit_offset(mq_message)

        if user and message and message.callback_id:
            self.remove_timer(message)

    def _get_valid_message_key(self, from_message: SmartAppFromMessage):
        return "_".join([i for i in [from_message.channel, from_message.sub, from_message.uid] if i])

    def _get_str_message_key(self, message_key: Union[str, bytes], incremental_id: int, uid: str, user: BaseUser):
        message_key = message_key or b""
        try:
            if isinstance(message_key, bytes):
                message_key = message_key.decode()
        except UnicodeDecodeError:
            log(f"MainLoop._get_str_message_key: Decode error of Kafka message key {message_key}",
                params={log_const.KEY_NAME: "check_kafka_key_error",
                        MESSAGE_ID_STR: incremental_id,
                        UID_STR: uid},
                user=user, level="ERROR")

        return message_key

    def _send_request(self, user: BaseUser, answer: SmartAppToMessage, mq_message: KafkaMessage):
        kafka_broker_settings = self.settings["template_settings"].get(
            "route_kafka_broker"
        ) or []

        request = answer.request

        for kb_setting in kafka_broker_settings:
            if (
                    kb_setting["from_channel"] == answer.incoming_message.channel and
                    kb_setting["to_topic"] == request.topic_key
            ):
                request.kafka_key = kb_setting["route_to_broker"]

        request_params = dict()
        request_params["publishers"] = self.publishers
        request_params["mq_message"] = mq_message
        request_params["payload"] = answer.value
        request_params["masked_value"] = answer.masked_value
        request.run(answer.value, request_params)
        self._log_request(user, request, answer, mq_message)

    def _log_request(self, user, request, answer, original_mq_message):
        log("OUTGOING TO TOPIC_KEY: %(topic_key)s DATA: %(data)s",
            params={log_const.KEY_NAME: "outgoing_message",
                    "topic_key": request.topic_key,
                    "headers": request._get_new_headers(original_mq_message),
                    "data": answer.masked_value,
                    "length": len(answer.value),
                    "message_key": (original_mq_message.key() or b"").decode('utf-8', 'backslashreplace')},
            user=user)

    @lru_cache()
    def _topic_names_2_key(self, kafka_key):
        topics = self.settings["kafka"]["template-engine"][kafka_key]["consumer"]["topics"]
        return {name: key for key, name in topics.items()}

    def default_topic_key(self, kafka_key):
        return self.settings["kafka"]["template-engine"][kafka_key].get("default_topic_key")

    @cached_property
    def masking_fields(self):
        return self.settings["template_settings"].get("masking_fields")

    def save_behavior_timeouts(self, user, mq_message: KafkaMessage, kafka_key):
        for i, (expire_time_us, callback_id) in enumerate(user.behaviors.get_behavior_timeouts()):
            # TODO: remove "- time()" when framework will be modified to asyncio only
            # если колбеков много, разносим их на 1 секунду друг от друга во избежание коллизий
            when = expire_time_us - time.time() + i
            log(f"%(class_name)s: adding local_timeout on callback %({log_const.BEHAVIOR_CALLBACK_ID_VALUE})s"
                " with timeout in %(when)s seconds.",
                params={log_const.KEY_NAME: "adding_local_timeout",
                        "class_name": self.__class__.__name__,
                        log_const.BEHAVIOR_CALLBACK_ID_VALUE: callback_id,
                        "when": when,
                        MESSAGE_ID_STR: user.message.incremental_id})

            kwargs = {"kafka_key": kafka_key,
                      "mq_message": mq_message,
                      "callback_id": callback_id,
                      "db_uid": user.message.db_uid}

            self._timers[callback_id] = self.loop.call_later(
                when, self.loop.create_task, self.put_to_queue(mq_message, self.do_behavior_timeout, kwargs)
            )

    async def do_behavior_timeout(self, kwargs, worker_kwargs):
        self.concurrent_messages += 1
        mq_message, kafka_key = kwargs.get("mq_message"), kwargs.get("kafka_key")
        callback_id, db_uid = kwargs.get("callback_id"), kwargs.get("db_uid")

        try:
            save_tries = 0
            user_save_ok = False
            answers = []
            user = None
            timeout_from_message = None
            callback_found = True
            while save_tries < self.user_save_collisions_tries and not user_save_ok:
                callback_found = False
                save_tries += 1
                orig_message_raw = json.loads(mq_message.value())
                orig_message_raw[SmartAppFromMessage.MESSAGE_NAME] = message_names.LOCAL_TIMEOUT
                timeout_from_message = self._get_timeout_from_message(orig_message_raw, callback_id,
                                                                      headers=mq_message.headers())

                log(f"MainLoop.do_behavior_timeout: handling callback {callback_id}. "
                    f"for db_uid {db_uid}. try {save_tries}.",
                    params={log_const.KEY_NAME: "MainLoop",
                            MESSAGE_ID_STR: timeout_from_message.incremental_id})
                user = await self.load_user(db_uid, timeout_from_message)

                if user.behaviors.has_callback(callback_id):
                    callback_found = True
                    topic_key = self._get_topic_key(mq_message, kafka_key)
                    async for command in self.model.answer(timeout_from_message, user):
                        answers = self._generate_answers(user=user, commands=[command], message=timeout_from_message,
                                                         topic_key=topic_key, kafka_key=kafka_key)
                        for answer in answers:
                            self._send_request(user, answer, mq_message)

                    user_save_ok = await self.save_user(db_uid, user, mq_message)

                    if user_save_ok:
                        self.save_behavior_timeouts(user, mq_message, kafka_key)
                    else:
                        log("MainLoop.do_behavior_timeout: save user got collision on uid %(uid)s db_version "
                            "%(db_version)s.",
                            user=user,
                            params={log_const.KEY_NAME: "ignite_collision",
                                    "db_uid": db_uid,
                                    "message_key": (mq_message.key() or b"").decode('utf-8', 'backslashreplace'),
                                    "kafka_key": kafka_key,
                                    "uid": user.id,
                                    "db_version": str(user.private_vars.get(user.USER_DB_VERSION))},
                            level="WARNING")
                else:
                    break

            self.remove_timer(timeout_from_message)

            if not user_save_ok and callback_found:
                log("MainLoop.do_behavior_timeout: db_save collision all tries left on uid %(uid)s db_version "
                    "%(db_version)s.",
                    user=user,
                    params={log_const.KEY_NAME: "ignite_collision",
                            "db_uid": db_uid,
                            "message_key": (mq_message.key() or b"").decode('utf-8', 'backslashreplace'),
                            "message_partition": mq_message.partition(),
                            "kafka_key": kafka_key,
                            "uid": user.id,
                            "db_version": str(user.private_vars.get(user.USER_DB_VERSION))},
                    level="WARNING")
                monitoring.counter_save_collision_tries_left(self.app_name)
        except Exception:
            log("%(class_name)s error.", params={log_const.KEY_NAME: "error_handling_timeout",
                                                 "class_name": self.__class__.__name__,
                                                 log_const.REQUEST_VALUE: str(mq_message.value())},
                level="ERROR", exc_info=True)
        finally:
            self.concurrent_messages -= 1

    def remove_timer(self, kafka_message):
        if kafka_message and kafka_message.has_callback_id:
            timer = self._timers.pop(kafka_message.callback_id, None)
            if timer is not None:
                log(f"Removing aio timer for callback {kafka_message.callback_id}. Have {len(self._timers)} running "
                    f"timers.", level="DEBUG")
                timer.cancel()

    def stop(self, signum, frame):
        log("Stop signal handler!")
        self.is_work = False

import inspect
import re
from functools import wraps

from core.logging.logger_constants import KEY_NAME
from core.logging.logger_utils import log

from prometheus_client import Counter, Histogram, REGISTRY


def _filter_monitoring_msg(msg):
    msg = msg.replace("-", ":")
    return msg


class MetricDisabled(ValueError):
    pass


def silence_it(func):
    def wrap(*args, **kwargs):
        try:
            func(*args, **kwargs)
        except MetricDisabled as error:
            log(f"Metrics: {error}",
                params={KEY_NAME: "metrics_disabled"}, level="DEBUG")
        except Exception:
            log("Metrics: Failed send. Exception occurred.",
                params={KEY_NAME: "metrics_fail"}, level="ERROR", exc_info=True)
    return wrap


class Monitoring:
    COUNTER = "counter"
    HISTOGRAM = "histogram"
    DEFAULT_ENABLED = True
    DEFAULT_DISABLED_METRICS = []

    def __init__(self):
        self._enabled = self.DEFAULT_ENABLED
        self.disabled_metrics = self.DEFAULT_DISABLED_METRICS.copy()
        self.buckets = Histogram.DEFAULT_BUCKETS
        self._monitoring_items = {
            self.COUNTER: {},
            self.HISTOGRAM: {}
        }
        self._clean_registry()

    @staticmethod
    def _clean_registry():
        """При создании нового инстанса мониторинга удаляем все созданные коллекторы"""
        collectors = list(REGISTRY._collector_to_names.keys())
        for collector in collectors:
            REGISTRY.unregister(collector)

    def check_enabled(self, name: str):
        metric_disabled = next((True for m in self.disabled_metrics if re.fullmatch(m, name)), False)
        return self._enabled and not metric_disabled

    def turn_on(self):
        self._enabled = True

    def turn_off(self):
        self._enabled = False

    def get_counter(self, name, description=None, labels=()):
        if not self.check_enabled(name):
            return None
        counter = self._monitoring_items[self.COUNTER]
        if not counter.get(name):
            counter[name] = Counter(name, description or name, labels)
        return counter[name]

    def got_counter(self, name, description=None, labels=()):
        counter = self.get_counter(name, description, labels)
        if counter:
            counter.inc()

    def got_histogram(self, name, description=None):
        def decor(func):
            def wrap(*args, **kwargs):
                decor_ = self._got_histogram(name, description=None)
                if decor_:
                    return decor_(func)(*args, **kwargs)
                else:
                    return func(*args, **kwargs)
            return wrap
        return decor

    def _got_histogram(self, name, description=None):
        if self.check_enabled(name):
            histogram = self._monitoring_items[self.HISTOGRAM]
            if not histogram.get(name):
                histogram[name] = Histogram(name, description or name, buckets=self.buckets)
            return histogram[name].time()

    def got_histogram_observe(self, name, value, description=None):
        if self.check_enabled(name):
            histogram = self._monitoring_items[self.HISTOGRAM]
            if not histogram.get(name):
                histogram[name] = Histogram(name, description or name, buckets=self.buckets)
            return histogram[name].observe(value)

    def apply_config(self, config):
        self._enabled = config.get("enabled", self.DEFAULT_ENABLED)
        self.disabled_metrics = config.get("disabled_metrics", self.DEFAULT_DISABLED_METRICS.copy())
        self.buckets = config.get("buckets", Histogram.DEFAULT_BUCKETS)

    @silence_it
    def init_metrics(self, app_name):
        self._get_or_create_counter(_filter_monitoring_msg(f"{app_name}_load_error"), "Load user data error")
        self._get_or_create_counter(_filter_monitoring_msg(f"{app_name}_save_error"), "Save user data error")
        self._get_or_create_counter(_filter_monitoring_msg(f"{app_name}_save_collision"),
                                    "Save user data collision")
        self._get_or_create_counter(_filter_monitoring_msg(f"{app_name}_save_collision_tries_left"),
                                    "Save user data collision all retries left.")
        self._get_or_create_counter(_filter_monitoring_msg(f"{app_name}_exception"), "Exception in run-time.")
        self._get_or_create_counter(_filter_monitoring_msg(f"{app_name}_invalid_message"),
                                    "Incoming message validation error.")

    def _get_or_create_counter(self, monitoring_msg, descr, labels=()):
        counter = monitoring.get_counter(monitoring_msg, descr, labels)
        if counter is None:
            raise MetricDisabled('counter disabled')
        return counter

    @silence_it
    def counter_incoming(self, app_name, message_name, handler, user, app_info=None):
        # REQ_IN_SUCCESS/REQ_IN_ERROR (пункты 3, 5 реестра метрик) покрыты существующими счётчиками:
        # incoming / invalid_message / exception / behavior_* — отдельных req_in-метрик не требуется.
        monitoring_msg = _filter_monitoring_msg(f"{app_name}_incoming")

        c = self._get_or_create_counter(monitoring_msg, "Count of incoming messages",
                                        ['message_name', 'handler', 'project_id', 'system_name', 'application_id',
                                         'app_version_id', 'channel', 'surface'])
        if app_info is not None:
            project_id = app_info.project_id
            system_name = app_info.system_name
            application_id = app_info.application_id
            app_version_id = app_info.app_version_id
        else:
            project_id = system_name = application_id = app_version_id = None
        c.labels(message_name, handler, project_id, system_name,
                 application_id, app_version_id, user.message.channel, user.message.device.surface).inc()

    @silence_it
    def counter_outgoing(self, app_name, message_name, outgoing_message, user):

        monitoring_msg = _filter_monitoring_msg(f"{app_name}_outgoing")

        c = self._get_or_create_counter(monitoring_msg, "Count of outgoing requests from application.",
                                        ['message_name', 'project_id', 'system_name', 'application_id',
                                         'app_version_id', 'channel', 'surface'])
        app_info = user.message.app_info
        c.labels(message_name, app_info.project_id, app_info.system_name,
                 app_info.application_id,
                 app_info.app_version_id, user.message.channel, user.message.device.surface).inc()

    @silence_it
    def counter_scenario_change(self, app_name, scenario, user):
        monitoring_msg = f"{app_name}_scenario_change"

        c = self._get_or_create_counter(monitoring_msg, "Count of scenario change events",
                                        ['scenario', 'project_id', 'system_name', 'application_id',
                                         'app_version_id', 'channel', 'surface'])
        app_info = user.message.app_info
        c.labels(scenario, app_info.project_id, app_info.system_name,
                 app_info.application_id,
                 app_info.app_version_id, user.message.channel, user.message.device.surface).inc()

    @silence_it
    def counter_nothing_found(self, app_name, scenario, user):
        monitoring_msg = f"{app_name}_outgoing_nothing_found"
        c = self._get_or_create_counter(monitoring_msg, "Count of scenario nothing found events",
                                        ['scenario', 'project_id', 'system_name', 'application_id',
                                         'app_version_id', 'channel', 'surface'])
        app_info = user.message.app_info
        c.labels(scenario, app_info.project_id, app_info.system_name,
                 app_info.application_id,
                 app_info.app_version_id, user.message.channel, user.message.device.surface).inc()

    @silence_it
    def counter_load_error(self, app_name):
        monitoring_msg = f"{app_name}_load_error"
        c = self._get_or_create_counter(_filter_monitoring_msg(monitoring_msg), "Load user data error")
        c.inc()

    @silence_it
    def counter_save_error(self, app_name):
        monitoring_msg = f"{app_name}_save_error"
        c = self._get_or_create_counter(_filter_monitoring_msg(monitoring_msg), "Save user data error")
        c.inc()

    @silence_it
    def counter_save_collision(self, app_name):
        monitoring_msg = f"{app_name}_save_collision"
        c = self._get_or_create_counter(_filter_monitoring_msg(monitoring_msg), "Save user data collision")
        c.inc()

    @silence_it
    def counter_save_collision_tries_left(self, app_name):
        monitoring_msg = f"{app_name}_save_collision_tries_left"
        c = self._get_or_create_counter(_filter_monitoring_msg(monitoring_msg),
                                        "Save user data collision all retries left.")
        c.inc()

    @silence_it
    def counter_exception(self, app_name):
        monitoring_msg = f"{app_name}_exception"
        c = self._get_or_create_counter(_filter_monitoring_msg(monitoring_msg), "Exception in run-time.")
        c.inc()

    @silence_it
    def counter_invalid_message(self, app_name):
        monitoring_msg = f"{app_name}_invalid_message"
        c = self._get_or_create_counter(_filter_monitoring_msg(monitoring_msg), "Incoming message validation error.")
        c.inc()

    @silence_it
    def counter_behavior_success(self, app_name, request_message_name):
        # 'Number of Success replies on messageName'
        self._behavior_monitoing_by_status(app_name, "success", request_message_name)

    @silence_it
    def counter_behavior_fail(self, app_name, request_message_name):
        # 'Number of Fail replies on messageName'
        self._behavior_monitoing_by_status(app_name, "fail", request_message_name)

    @silence_it
    def counter_behavior_misstate(self, app_name, request_message_name):
        # 'Number of Misstate replies on messageName'
        self._behavior_monitoing_by_status(app_name, "misstate", request_message_name)

    @silence_it
    def counter_behavior_timeout(self, app_name, request_message_name):
        # 'Number of Timeout replies on messageName'
        self._behavior_monitoing_by_status(app_name, "timeout", request_message_name)

    @silence_it
    def counter_behavior_expire(self, app_name, request_message_name):
        # 'Number of expire events on messageName'
        self._behavior_monitoing_by_status(app_name, "expire", request_message_name)

    def _behavior_monitoing_by_status(self, app_name, status, request_message_name):
        monitoring_msg = f'{app_name}_callback'
        c = self._get_or_create_counter(monitoring_msg,
                                        "Count of incoming callback events with request_message_name",
                                        ['request_message_name', 'status'])

        c.labels(request_message_name, status).inc()

    @silence_it
    def counter_host_has_changed(self, app_name):
        monitoring_msg = f'{app_name}_host_has_changed'
        c = self._get_or_create_counter(monitoring_msg,
                                        "Count of host has changed events within one message_id")
        c.inc()

    @silence_it
    def counter_mq_long_waiting(self, app_name):
        monitoring_msg = f"{app_name}_mq_long_waiting"
        c = self._get_or_create_counter(_filter_monitoring_msg(monitoring_msg),
                                        "(Now - creation_time) is greater than threshold")
        c.inc()

    @silence_it
    def sampling_load_time(self, app_name, value):
        monitoring_msg = f"{app_name}_load_time"
        monitoring.got_histogram_observe(_filter_monitoring_msg(monitoring_msg), value)

    @silence_it
    def sampling_script_time(self, app_name, value):
        monitoring_msg = f"{app_name}_script_time"
        monitoring.got_histogram_observe(_filter_monitoring_msg(monitoring_msg), value)

    @silence_it
    def sampling_save_time(self, app_name, value):
        monitoring_msg = f"{app_name}_save_time"
        monitoring.got_histogram_observe(_filter_monitoring_msg(monitoring_msg), value)

    @silence_it
    def sampling_total_time(self, app_name, value):
        monitoring_msg = f"{app_name}_total_time"
        monitoring.got_histogram_observe(_filter_monitoring_msg(monitoring_msg), value)

    @silence_it
    def sampling_mq_waiting_time(self, app_name, value):
        monitoring_msg = f"{app_name}_mq_waiting_time"
        monitoring.got_histogram_observe(_filter_monitoring_msg(monitoring_msg), value)

    @silence_it
    def counter_mq_skip_waiting(self, app_name):
        monitoring_msg = f"{app_name}_mq_skip_waiting"
        c = self._get_or_create_counter(monitoring_msg, "(Now - creation_time) is greater than error threshold")
        c.inc()

    @silence_it
    def pod_event(self, app_name, event_type):
        monitoring_msg = f"{app_name}_pod_event"
        c = self._get_or_create_counter(monitoring_msg, "Count of pod events by type", ['event_type'])
        c.labels(event_type).inc()

    @silence_it
    def counter_req_out_success(self, app_name, integration_name):
        """integration_name должен быть статичным идентификатором интеграции из конфигурации сценария."""
        monitoring_msg = f"{app_name}_req_out_success"
        c = self._get_or_create_counter(_filter_monitoring_msg(monitoring_msg),
                                        "Count of successful outgoing requests to external services.",
                                        ['integration_name'])
        c.labels(str(integration_name)).inc()

    @silence_it
    def counter_req_out_error(self, app_name, integration_name):
        monitoring_msg = f"{app_name}_req_out_error"
        c = self._get_or_create_counter(_filter_monitoring_msg(monitoring_msg),
                                        "Count of failed outgoing requests to external services.",
                                        ['integration_name'])
        c.labels(str(integration_name)).inc()

    @silence_it
    def counter_req_out_retry(self, app_name, integration_name, reason):
        monitoring_msg = f"{app_name}_req_out_retry"
        c = self._get_or_create_counter(_filter_monitoring_msg(monitoring_msg),
                                        "Count of retried outgoing requests to external services.",
                                        ['integration_name', 'reason'])
        c.labels(str(integration_name), str(reason)).inc()

    def req_out(self, integration_name, app_name=None):
        """Декоратор метрик req_out_success / req_out_error (4, 6 из реестра).

        Можно использовать отдельно от http-вызовов. Поддерживает обычные и async-функции.
        Сбой отправки метрик не влияет на оборачиваемый вызов.

        :param integration_name: статичный идентификатор интеграции (лейбл integration_name).
        :param app_name: имя приложения; по умолчанию APP_NAME из app_config, затем "unknown".
        """

        def emit(success):
            try:
                from smart_kit.configs import get_app_config
                app = app_name or getattr(get_app_config(), "APP_NAME", None) or "unknown"
                # через прокси monitoring: резолвим текущий инстанс на каждый вызов,
                # декоратор не должен биндить инстанс на момент декорирования
                if success:
                    monitoring.counter_req_out_success(app, integration_name)
                else:
                    monitoring.counter_req_out_error(app, integration_name)
            except Exception:
                log("Metrics: Failed send. Exception occurred.",
                    params={KEY_NAME: "metrics_fail"}, level="ERROR", exc_info=True)

        def decor(func):
            if inspect.iscoroutinefunction(func):
                @wraps(func)
                async def wrap(*args, **kwargs):
                    try:
                        result = await func(*args, **kwargs)
                    except Exception:
                        emit(False)
                        raise
                    emit(True)
                    return result
            else:
                @wraps(func)
                def wrap(*args, **kwargs):
                    try:
                        result = func(*args, **kwargs)
                    except Exception:
                        emit(False)
                        raise
                    emit(True)
                    return result
            return wrap
        return decor


class MonitoringProxy:
    def __init__(self, default_cls):
        self.instance = default_cls()

    def got_histogram(self, *args_, **kwargs_):
        def decor_(func):
            def wrap(*args, **kwargs):
                wrapped_func = self.instance.got_histogram(*args_, **kwargs_)(func)
                value = wrapped_func(*args, **kwargs)
                return value
            return wrap
        return decor_

    def set_instance(self, cls):
        if type(self.instance) != cls:
            self.instance = cls()

    def __getattr__(self, item):
        return getattr(self.instance, item)


monitoring = MonitoringProxy(Monitoring)

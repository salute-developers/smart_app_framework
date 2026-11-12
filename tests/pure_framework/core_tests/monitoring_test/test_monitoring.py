import asyncio
import unittest

from prometheus_client import Counter, Histogram

from core.monitoring.monitoring import Monitoring
from smart_kit.utils.picklable_mock import PicklableMock


class MonitoringTest(unittest.TestCase):
    def setUp(self):
        self.logger = PicklableMock()
        self.logger.exception = PicklableMock()
        self.config = PicklableMock()
        self.mock_rep = PicklableMock()
        self.monitoring = Monitoring()
        self.monitoring.apply_config({})

    def test_got_message_disabled(self):
        self.monitoring.turn_off()
        event_name = "test_counter"
        counter_item = self.monitoring._monitoring_items[self.monitoring.COUNTER]
        self.assertTrue(counter_item == dict())
        self.monitoring.got_counter(event_name)
        self.assertTrue(event_name not in counter_item)
        self.assertEqual(counter_item.get(event_name), None)

    def test_got_message_enabled(self):
        self.monitoring.turn_on()
        event_name = "test_counter"
        counter_item = self.monitoring._monitoring_items[self.monitoring.COUNTER]
        self.assertTrue(counter_item == dict())
        self.monitoring.got_counter(event_name)
        self.assertTrue(event_name in counter_item)
        self.assertEqual(type(counter_item[event_name]), type(Counter('counter_name', 'counter_name')))

    def test_got_histogram_disabled(self):
        self.monitoring.turn_off()
        event_name = "test_histogram"
        histogram_item = self.monitoring._monitoring_items[self.monitoring.HISTOGRAM]
        self.assertTrue(histogram_item == dict())
        histogram = self.monitoring._got_histogram(event_name)
        self.assertTrue(event_name not in histogram_item)
        self.assertIsNone(histogram)

    def test_got_histogram_enabled(self):
        self.monitoring.turn_on()
        event_name = "test_histogram"
        histogram_item = self.monitoring._monitoring_items[self.monitoring.HISTOGRAM]
        self.assertTrue(histogram_item == dict())
        self.monitoring._got_histogram(event_name)
        histogram_item = self.monitoring._monitoring_items[self.monitoring.HISTOGRAM]
        self.assertTrue(event_name in histogram_item)
        self.assertEqual(type(histogram_item[event_name]), type(Histogram('histogram_name', 'histogram_name')))

    def test_got_histogram_disabled_by_name(self):
        self.monitoring.turn_on()
        self.monitoring.disabled_metrics.append('test_.*')
        self.monitoring.disabled_metrics.append('.*_all')
        for event_name, disabled in [("test_one", True), ("test_two", True),
                                     ("not_a_test", False), ('metric_all', True)]:
            counter_item = self.monitoring._monitoring_items[self.monitoring.COUNTER]
            self.assertTrue(isinstance(counter_item, dict), event_name)
            self.monitoring.got_counter(event_name)
            if disabled:
                self.assertTrue(event_name not in counter_item, event_name)
            else:
                self.assertTrue(event_name in counter_item, event_name)

    def test_monitoring_init(self):
        from core.monitoring.monitoring import monitoring

        class MyCustomMonitoring(Monitoring):
            pass

        monitoring.set_instance(MyCustomMonitoring)
        self.assertEqual(type(monitoring.instance), MyCustomMonitoring)

        monitoring.set_instance(Monitoring)
        self.assertEqual(type(monitoring.instance), Monitoring)

    def test_decorator(self):
        from core.monitoring.monitoring import monitoring

        class MyCustomMonitoring(Monitoring):
            def got_histogram(self, name, description=None):
                def decorator(function):
                    def wrapper(*args, **kwargs):
                        result = function(*args, **kwargs) + " " + name
                        return result

                    return wrapper

                return decorator

        class SomeClass:
            @monitoring.got_histogram("test_histogram")
            def some_method(self):
                return "test"

        obj = SomeClass()
        self.assertEqual(obj.some_method(), "test")

        monitoring.set_instance(MyCustomMonitoring)
        self.assertEqual(obj.some_method(), "test test_histogram")

        monitoring.set_instance(Monitoring)
        self.assertEqual(obj.some_method(), "test")

        self.assertIn('test_histogram', monitoring._monitoring_items[Monitoring.HISTOGRAM].keys())

    def test_req_out_counters(self):
        from core.monitoring.monitoring import monitoring

        monitoring.set_instance(Monitoring)
        instance = monitoring.instance
        instance._enabled = True
        instance.disabled_metrics = []
        instance._monitoring_items = {instance.COUNTER: {}, instance.HISTOGRAM: {}}
        Monitoring._clean_registry()

        instance.counter_req_out_success("test_app", "isearch")
        instance.counter_req_out_error("test_app", "isearch")
        counter_item = instance._monitoring_items[instance.COUNTER]
        self.assertIn("test_app_req_out_success", counter_item)
        self.assertIn("test_app_req_out_error", counter_item)
        self.assertEqual(counter_item["test_app_req_out_success"]._labelnames, ("integration_name",))
        self.assertEqual(
            counter_item["test_app_req_out_success"]._metrics[("isearch",)]._value.get(), 1.0)
        self.assertEqual(
            counter_item["test_app_req_out_error"]._metrics[("isearch",)]._value.get(), 1.0)

    def test_req_out_decorator_sync(self):
        from core.monitoring.monitoring import monitoring

        monitoring.set_instance(Monitoring)
        instance = monitoring.instance
        instance._enabled = True
        instance.disabled_metrics = []
        instance._monitoring_items = {instance.COUNTER: {}, instance.HISTOGRAM: {}}
        Monitoring._clean_registry()

        @instance.req_out(integration_name="isearch", app_name="test_app")
        def ok_func():
            return "ok"

        @instance.req_out(integration_name="isearch", app_name="test_app")
        def fail_func():
            raise ValueError("fail")

        self.assertEqual(ok_func(), "ok")
        with self.assertRaises(ValueError):
            fail_func()
        counter_item = instance._monitoring_items[instance.COUNTER]
        self.assertEqual(
            counter_item["test_app_req_out_success"]._metrics[("isearch",)]._value.get(), 1.0)
        self.assertEqual(
            counter_item["test_app_req_out_error"]._metrics[("isearch",)]._value.get(), 1.0)

    def test_req_out_decorator_async(self):
        from core.monitoring.monitoring import monitoring

        monitoring.set_instance(Monitoring)
        instance = monitoring.instance
        instance._enabled = True
        instance.disabled_metrics = []
        instance._monitoring_items = {instance.COUNTER: {}, instance.HISTOGRAM: {}}
        Monitoring._clean_registry()

        @instance.req_out(integration_name="ihapi", app_name="test_app")
        async def ok_func():
            return "ok"

        @instance.req_out(integration_name="ihapi", app_name="test_app")
        async def fail_func():
            raise ValueError("fail")

        async def run():
            self.assertEqual(await ok_func(), "ok")
            with self.assertRaises(ValueError):
                await fail_func()

        asyncio.run(run())
        counter_item = instance._monitoring_items[instance.COUNTER]
        self.assertEqual(
            counter_item["test_app_req_out_success"]._metrics[("ihapi",)]._value.get(), 1.0)
        self.assertEqual(
            counter_item["test_app_req_out_error"]._metrics[("ihapi",)]._value.get(), 1.0)

    def test_req_out_decorator_emit_failure_does_not_break_call(self):
        """Сбой отправки метрик (например, get_app_config бросил исключение) не должен уронить бизнес-вызов."""
        from unittest.mock import patch

        from core.monitoring.monitoring import monitoring

        monitoring.set_instance(Monitoring)
        instance = monitoring.instance
        instance._enabled = True
        instance.disabled_metrics = []
        instance._monitoring_items = {instance.COUNTER: {}, instance.HISTOGRAM: {}}
        Monitoring._clean_registry()

        @instance.req_out(integration_name="isearch")
        def ok_func():
            return "ok"

        with patch("smart_kit.configs.get_app_config", side_effect=AttributeError("not configured")):
            self.assertEqual(ok_func(), "ok")

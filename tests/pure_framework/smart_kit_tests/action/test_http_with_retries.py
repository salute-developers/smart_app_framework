import unittest
from unittest.mock import Mock, patch, AsyncMock

import aiohttp

from smart_kit.action.http import HTTPRequestAction
from smart_kit.action.http_with_retries import HTTPRequestActionWithRetries
from tests.pure_framework.smart_kit_tests.action.http_test_utils import (
    make_response_context,
    make_settings_mock,
    make_timeout_context,
)


class HttpRequestActionWithRetriesTest(unittest.IsolatedAsyncioTestCase):
    TIMEOUT = 3

    def setUp(self):
        self.settings = make_settings_mock()
        self.user = Mock(
            settings=self.settings,
            parametrizer=Mock(collect=lambda *args, **kwargs: {}),
            descriptions={
                "behaviors": {
                    "my_behavior": AsyncMock(timeout=Mock(return_value=3))
                }
            }
        )

    @staticmethod
    def set_request_mock_attribute(request_mock, return_value=None, status=200):
        context, response = make_response_context(status=status, data=return_value)
        request_mock.return_value = context
        return response

    @staticmethod
    def make_items(**extra_params):
        params = {
            "method": "POST",
            "url": "https://my.url.com",
            "timeout": 3,
        }
        params.update(extra_params)
        return {
            "params": params,
            "store": "user_variable",
            "behavior": "my_behavior",
        }

    @patch('smart_kit.action.http.monitoring')
    @patch('aiohttp.request')
    async def test_success_first_attempt(self, request_mock, monitoring_mock):
        self.set_request_mock_attribute(request_mock, return_value={'data': 'value'})
        items = self.make_items(integration_name="isearch")
        await HTTPRequestActionWithRetries(items).run(self.user, None, {})
        self.assertEqual(request_mock.call_count, 1)
        self.user.variables.set.assert_called_with("user_variable", {'data': 'value'})
        monitoring_mock.counter_req_out_success.assert_called_once_with("test_app", "isearch")
        monitoring_mock.counter_req_out_error.assert_not_called()

    @patch('smart_kit.action.http.monitoring')
    @patch('aiohttp.request')
    async def test_integration_name_fallback_to_id(self, request_mock, monitoring_mock):
        self.set_request_mock_attribute(request_mock, return_value={'data': 'value'})
        items = self.make_items()
        await HTTPRequestActionWithRetries(items, id="my_action").run(self.user, None, {})
        monitoring_mock.counter_req_out_success.assert_called_once_with("test_app", "my_action")

    @patch('smart_kit.action.http.monitoring')
    @patch('aiohttp.request')
    async def test_integration_name_not_passed_to_aiohttp(self, request_mock, monitoring_mock):
        self.set_request_mock_attribute(request_mock, return_value={'data': 'value'})
        items = self.make_items(integration_name="isearch")
        await HTTPRequestActionWithRetries(items).run(self.user, None, {})
        self.assertNotIn("integration_name", request_mock.call_args.kwargs)

    @patch('smart_kit.action.http_with_retries.monitoring')
    @patch('smart_kit.action.http.monitoring')
    @patch('aiohttp.request')
    async def test_timeout_then_success(self, request_mock, http_monitoring_mock, retry_monitoring_mock):
        context, response = make_response_context(data={'data': 'value'})
        request_mock.side_effect = [aiohttp.ServerTimeoutError(), context]
        items = self.make_items(integration_name="isearch")
        action = HTTPRequestActionWithRetries(items)
        await action.run(self.user, None, {})
        self.assertEqual(request_mock.call_count, 2)
        self.user.variables.set.assert_called_with("user_variable", {'data': 'value'})
        http_monitoring_mock.counter_req_out_success.assert_called_once()
        http_monitoring_mock.counter_req_out_error.assert_not_called()
        retry_monitoring_mock.counter_req_out_retry.assert_called_once_with("test_app", "isearch", "TIMEOUT")

    @patch('smart_kit.action.http_with_retries.monitoring')
    @patch('smart_kit.action.http.monitoring')
    @patch('aiohttp.request')
    async def test_timeout_all_attempts(self, request_mock, http_monitoring_mock, retry_monitoring_mock):
        """3 неудачные попытки = 2 реальных ретрая: лог и метрика retry не должны считаться на последней."""
        request_mock.side_effect = aiohttp.ServerTimeoutError()
        items = self.make_items(integration_name="isearch")
        action = HTTPRequestActionWithRetries(items)
        await action.run(self.user, None, {})
        self.assertEqual(request_mock.call_count, HTTPRequestActionWithRetries.DEFAULT_MAX_ATTEMPTS)
        self.assertTrue(self.user.descriptions["behaviors"]["my_behavior"].timeout_action.run.called)
        self.assertFalse(self.user.variables.set.called)
        http_monitoring_mock.counter_req_out_error.assert_called_once_with("test_app", "isearch")
        http_monitoring_mock.counter_req_out_success.assert_not_called()
        self.assertEqual(retry_monitoring_mock.counter_req_out_retry.call_count, 2)

    @patch('smart_kit.action.http_with_retries.monitoring')
    @patch('smart_kit.action.http.monitoring')
    @patch('aiohttp.request')
    async def test_connection_error_then_success(self, request_mock, http_monitoring_mock, retry_monitoring_mock):
        context, response = make_response_context(data={'data': 'value'})
        request_mock.side_effect = [
            aiohttp.ClientConnectorError(connection_key=Mock(), os_error=OSError(1, "connection refused")),
            context,
        ]
        items = self.make_items(integration_name="isearch")
        await HTTPRequestActionWithRetries(items).run(self.user, None, {})
        self.assertEqual(request_mock.call_count, 2)
        self.user.variables.set.assert_called_with("user_variable", {'data': 'value'})
        http_monitoring_mock.counter_req_out_success.assert_called_once()
        retry_monitoring_mock.counter_req_out_retry.assert_called_once_with("test_app", "isearch", "CONNECTION")

    @patch('smart_kit.action.http_with_retries.monitoring')
    @patch('smart_kit.action.http.monitoring')
    @patch('aiohttp.request')
    async def test_retryable_status_then_success(self, request_mock, http_monitoring_mock, retry_monitoring_mock):
        bad_context, _ = make_response_context(status=429)
        good_context, _ = make_response_context(data={'data': 'value'})
        request_mock.side_effect = [bad_context, good_context]
        items = self.make_items(integration_name="isearch")
        await HTTPRequestActionWithRetries(items).run(self.user, None, {})
        self.assertEqual(request_mock.call_count, 2)
        self.user.variables.set.assert_called_with("user_variable", {'data': 'value'})
        http_monitoring_mock.counter_req_out_success.assert_called_once()
        retry_monitoring_mock.counter_req_out_retry.assert_called_once_with("test_app", "isearch", 429)

    @patch('smart_kit.action.http_with_retries.monitoring')
    @patch('smart_kit.action.http.monitoring')
    @patch('aiohttp.request')
    async def test_retryable_status_all_attempts(self, request_mock, http_monitoring_mock, retry_monitoring_mock):
        """3 ответа 429 = 2 реальных ретрая; на последней попытке retry не логируется и не считается."""
        bad_context, _ = make_response_context(status=429)
        request_mock.return_value = bad_context
        items = self.make_items(integration_name="isearch")
        action = HTTPRequestActionWithRetries(items)
        await action.run(self.user, None, {})
        self.assertEqual(request_mock.call_count, HTTPRequestActionWithRetries.DEFAULT_MAX_ATTEMPTS)
        # последний неудачный ответ завершается так же, как в базовом классе (raise_for_status -> CONNECTION)
        self.assertTrue(self.user.descriptions["behaviors"]["my_behavior"].fail_action.run.called)
        self.assertFalse(self.user.variables.set.called)
        http_monitoring_mock.counter_req_out_error.assert_called_once_with("test_app", "isearch")
        self.assertEqual(retry_monitoring_mock.counter_req_out_retry.call_count, 2)

    @patch('smart_kit.action.http.monitoring')
    @patch('aiohttp.request')
    async def test_non_retryable_status_not_retried(self, request_mock, http_monitoring_mock):
        self.set_request_mock_attribute(request_mock, status=500)
        items = self.make_items(integration_name="isearch")
        action = HTTPRequestActionWithRetries(items)
        await action.run(self.user, None, {})
        self.assertEqual(request_mock.call_count, 1)
        self.assertTrue(self.user.descriptions["behaviors"]["my_behavior"].fail_action.run.called)
        self.assertFalse(self.user.variables.set.called)
        http_monitoring_mock.counter_req_out_error.assert_called_once_with("test_app", "isearch")

    @patch('smart_kit.action.http.monitoring')
    @patch('aiohttp.request')
    async def test_max_attempts_from_template_settings(self, request_mock, monitoring_mock):
        self.settings.__getitem__.return_value = {"http_request_max_attempts": 2}
        request_mock.side_effect = aiohttp.ServerTimeoutError()
        items = self.make_items(integration_name="isearch")
        await HTTPRequestActionWithRetries(items).run(self.user, None, {})
        self.assertEqual(request_mock.call_count, 2)
        monitoring_mock.counter_req_out_error.assert_called_once()

    @patch('smart_kit.action.http.monitoring')
    @patch('aiohttp.request')
    async def test_zero_retries_means_single_attempt(self, request_mock, http_monitoring_mock):
        """Некорректное значение http_request_max_attempts <= 0 не должно отменять запрос."""
        self.settings.__getitem__.return_value = {"http_request_max_attempts": 0}
        request_mock.side_effect = aiohttp.ServerTimeoutError()
        items = self.make_items(integration_name="isearch")
        action = HTTPRequestActionWithRetries(items)
        await action.run(self.user, None, {})
        self.assertEqual(request_mock.call_count, 1)
        self.assertTrue(self.user.descriptions["behaviors"]["my_behavior"].timeout_action.run.called)
        http_monitoring_mock.counter_req_out_error.assert_called_once()

    @patch('smart_kit.action.http.monitoring')
    @patch('aiohttp.request')
    async def test_non_numeric_retries_falls_back_to_default(self, request_mock, monitoring_mock):
        self.settings.__getitem__.return_value = {"http_request_max_attempts": "abc"}
        request_mock.side_effect = aiohttp.ServerTimeoutError()
        items = self.make_items(integration_name="isearch")
        await HTTPRequestActionWithRetries(items).run(self.user, None, {})
        self.assertEqual(request_mock.call_count, HTTPRequestActionWithRetries.DEFAULT_MAX_ATTEMPTS)
        monitoring_mock.counter_req_out_error.assert_called_once()

    @patch('smart_kit.action.http.monitoring')
    @patch('aiohttp.request')
    async def test_retry_statuses_from_template_settings(self, request_mock, monitoring_mock):
        self.settings.__getitem__.return_value = {"http_request_retry_statuses": [500]}
        bad_context, _ = make_response_context(status=500)
        good_context, _ = make_response_context(data={'data': 'value'})
        request_mock.side_effect = [bad_context, good_context]
        items = self.make_items(integration_name="isearch")
        await HTTPRequestActionWithRetries(items).run(self.user, None, {})
        self.assertEqual(request_mock.call_count, 2)
        monitoring_mock.counter_req_out_success.assert_called_once()

    @patch('smart_kit.action.http.monitoring')
    @patch('aiohttp.request')
    async def test_scalar_retry_status_from_template_settings(self, request_mock, monitoring_mock):
        """Скаляр в http_request_retry_statuses (YAML без списка) не должен ронять действие."""
        self.settings.__getitem__.return_value = {"http_request_retry_statuses": 429}
        bad_context, _ = make_response_context(status=429)
        good_context, _ = make_response_context(data={'data': 'value'})
        request_mock.side_effect = [bad_context, good_context]
        items = self.make_items(integration_name="isearch")
        await HTTPRequestActionWithRetries(items).run(self.user, None, {})
        self.assertEqual(request_mock.call_count, 2)
        monitoring_mock.counter_req_out_success.assert_called_once()

    @patch('smart_kit.action.http.monitoring')
    @patch('aiohttp.request')
    async def test_string_retry_status_normalized(self, request_mock, monitoring_mock):
        """Строковые статусы из YAML нормализуются к int и матчатся с response.status."""
        self.settings.__getitem__.return_value = {"http_request_retry_statuses": ["429"]}
        bad_context, _ = make_response_context(status=429)
        good_context, _ = make_response_context(data={'data': 'value'})
        request_mock.side_effect = [bad_context, good_context]
        items = self.make_items(integration_name="isearch")
        await HTTPRequestActionWithRetries(items).run(self.user, None, {})
        self.assertEqual(request_mock.call_count, 2)
        monitoring_mock.counter_req_out_success.assert_called_once()

    @patch('asyncio.sleep', new_callable=AsyncMock)
    @patch('smart_kit.action.http.monitoring')
    @patch('aiohttp.request')
    async def test_retry_delay_from_template_settings(self, request_mock, monitoring_mock, sleep_mock):
        self.settings.__getitem__.return_value = {"http_request_retry_delay": 0.5}
        context, _ = make_response_context(data={'data': 'value'})
        request_mock.side_effect = [aiohttp.ServerTimeoutError(), context]
        items = self.make_items(integration_name="isearch")
        await HTTPRequestActionWithRetries(items).run(self.user, None, {})
        self.assertEqual(request_mock.call_count, 2)
        sleep_mock.assert_called_once_with(0.5)
        monitoring_mock.counter_req_out_success.assert_called_once()

    @patch('smart_kit.action.http.monitoring')
    @patch('aiohttp.request')
    async def test_success_after_failed_attempt_clears_error(self, request_mock, http_monitoring_mock):
        """Успешная попытка после неудачной должна привести к success-ветке process_result."""
        context, response = make_response_context(data={'data': 'value'})
        request_mock.side_effect = [aiohttp.ServerTimeoutError(), context]
        items = self.make_items(integration_name="isearch")
        action = HTTPRequestActionWithRetries(items)
        await action.run(self.user, None, {})
        self.assertTrue(
            self.user.descriptions["behaviors"]["my_behavior"].success_action.run.called)

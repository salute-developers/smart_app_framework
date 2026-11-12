import asyncio
import unittest
from unittest.mock import Mock, patch, AsyncMock

import aiohttp
from aiohttp import ClientTimeout

from smart_kit.action.http import HTTPRequestAction
from tests.pure_framework.smart_kit_tests.action.http_test_utils import (
    make_response_context,
    make_settings_mock,
    make_timeout_context,
)


class HttpRequestActionTest(unittest.IsolatedAsyncioTestCase):
    TIMEOUT = 3

    def setUp(self):
        self.user = Mock(
            settings=make_settings_mock(),
            parametrizer=Mock(collect=lambda *args, **kwargs: {}),
            descriptions={
                "behaviors": {
                    "my_behavior": AsyncMock(timeout=Mock(return_value=3))
                }
            }
        )

    @staticmethod
    def set_request_mock_attribute(request_mock, return_value=None):
        context, _ = make_response_context(data=return_value)
        request_mock.return_value = context

    @patch('aiohttp.request')
    async def test_simple_request(self, request_mock: Mock):
        self.set_request_mock_attribute(request_mock, return_value={'data': 'value'})
        items = {
            "params": {
                "method": "POST",
                "url": "https://my.url.com",
            },
            "store": "user_variable",
            "behavior": "my_behavior",
        }
        await HTTPRequestAction(items).run(self.user, None, {})
        request_mock.assert_called_with(url="https://my.url.com", method='POST', timeout=ClientTimeout(3))
        self.assertTrue(self.user.descriptions["behaviors"]["my_behavior"].success_action.run.called)
        self.assertTrue(self.user.variables.set.called)
        self.user.variables.set.assert_called_with("user_variable", {'data': 'value'})

    @patch('aiohttp.request')
    async def test_render_params(self, request_mock: Mock):
        self.set_request_mock_attribute(request_mock)
        items = {
            "params": {
                "method": "POST",
                "url": "https://{{url}}",
                "timeout": 3,
                "json": {
                    "param": "{{value}}"
                }
            },
            "store": "user_variable",
            "behavior": "my_behavior",
        }
        params = {
            "url": "my.url.com",
            "value": "my_value"
        }
        await HTTPRequestAction(items).run(self.user, None, params)
        request_mock.assert_called_with(
            url="https://my.url.com", method='POST', timeout=ClientTimeout(3), json={"param": "my_value"}
        )

    @patch('aiohttp.request')
    async def test_headers_fix(self, request_mock):
        self.set_request_mock_attribute(request_mock)
        items = {
            "params": {
                "headers": {
                    "header_1": 32,
                    "header_2": 32.03,
                    "header_3": b"d32",
                    "header_4": None,
                    "header_5": {"data": "value"},
                },
            },
            "store": "user_variable",
            "behavior": "my_behavior",
        }
        await HTTPRequestAction(items).run(self.user, None, {})
        request_mock.assert_called_with(headers={
            "header_1": "32",
            "header_2": "32.03",
            "header_3": b"d32"
        }, method=HTTPRequestAction.DEFAULT_METHOD, timeout=ClientTimeout(self.TIMEOUT))

    @patch('aiohttp.request')
    async def test_behavior_is_none(self, request_mock):
        self.set_request_mock_attribute(request_mock)
        items = {
            "params": {
            },
            "store": "user_variable",
        }
        await HTTPRequestAction(items).run(self.user, None, {})
        request_mock.assert_called_with(method=HTTPRequestAction.DEFAULT_METHOD,
                                        timeout=ClientTimeout(HTTPRequestAction.DEFAULT_TIMEOUT))

    @patch('smart_kit.action.http.monitoring')
    @patch('aiohttp.request')
    async def test_req_out_success_metric(self, request_mock, monitoring_mock):
        self.set_request_mock_attribute(request_mock, return_value={'data': 'value'})
        items = {
            "params": {
                "method": "POST",
                "url": "https://my.url.com",
                "integration_name": "isearch",
            },
            "store": "user_variable",
            "behavior": "my_behavior",
        }
        await HTTPRequestAction(items).run(self.user, None, {})
        monitoring_mock.counter_req_out_success.assert_called_once_with("test_app", "isearch")
        monitoring_mock.counter_req_out_error.assert_not_called()

    @patch('smart_kit.action.http.monitoring')
    @patch('aiohttp.request')
    async def test_req_out_success_metric_for_null_body(self, request_mock, monitoring_mock):
        """Ответ 2xx с телом null (json вернёт None) не должен считаться ошибкой в метрике."""
        context, _ = make_response_context(data=None)
        request_mock.return_value = context
        items = {
            "params": {
                "method": "POST",
                "url": "https://my.url.com",
                "integration_name": "isearch",
            },
            "store": "user_variable",
            "behavior": "my_behavior",
        }
        await HTTPRequestAction(items).run(self.user, None, {})
        monitoring_mock.counter_req_out_success.assert_called_once_with("test_app", "isearch")
        monitoring_mock.counter_req_out_error.assert_not_called()

    @patch('smart_kit.action.http.monitoring')
    @patch('aiohttp.request')
    async def test_req_out_error_metric(self, request_mock, monitoring_mock):
        request_mock.side_effect = aiohttp.ServerTimeoutError()
        items = {
            "params": {
                "method": "POST",
                "url": "https://my.url.com",
                "integration_name": "isearch",
            },
            "store": "user_variable",
            "behavior": "my_behavior",
        }
        action = HTTPRequestAction(items)
        await action.run(self.user, None, {})
        self.assertTrue(self.user.descriptions["behaviors"]["my_behavior"].timeout_action.run.called)
        self.assertFalse(self.user.variables.set.called)
        monitoring_mock.counter_req_out_error.assert_called_once_with("test_app", "isearch")
        monitoring_mock.counter_req_out_success.assert_not_called()

    @patch('smart_kit.action.http.monitoring')
    @patch('aiohttp.request')
    async def test_error_reset_between_runs(self, request_mock, monitoring_mock):
        """Экземпляры действий общие для всех юзеров и сообщений: ошибка одного вызова не должна
        «заражать» последующие вызовы того же действия."""
        items = {
            "params": {
                "method": "POST",
                "url": "https://my.url.com",
                "integration_name": "isearch",
            },
            "store": "user_variable",
            "behavior": "my_behavior",
        }
        action = HTTPRequestAction(items)

        # первый вызов: таймаут
        request_mock.side_effect = aiohttp.ServerTimeoutError()
        await action.run(self.user, None, {})
        monitoring_mock.counter_req_out_error.assert_called_once()
        timeout_action = self.user.descriptions["behaviors"]["my_behavior"].timeout_action
        self.assertTrue(timeout_action.run.called)

        # второй вызов того же экземпляра: успех
        context, _ = make_response_context(data={'data': 'value'})
        request_mock.side_effect = None
        request_mock.return_value = context
        await action.run(self.user, None, {})
        self.user.variables.set.assert_called_with("user_variable", {'data': 'value'})
        success_action = self.user.descriptions["behaviors"]["my_behavior"].success_action
        self.assertTrue(success_action.run.called)
        monitoring_mock.counter_req_out_success.assert_called_once()
        self.assertEqual(monitoring_mock.counter_req_out_error.call_count, 1)

    @patch('smart_kit.action.http.monitoring')
    @patch('aiohttp.request')
    async def test_concurrent_runs_isolated_error(self, request_mock, monitoring_mock):
        """Гоночный случай: конкурентные run() одного экземпляра не должны подменять ошибки друг другу.

        Опасный интервал — успешный вызов припаркован на await response.json(), а другой вызов
        в это время пишет ошибку: на старом коде (ошибка в self) успех «протухал» в ошибку."""
        items = {
            "params": {
                "method": "POST",
                "url": "https://my.url.com",
                "integration_name": "isearch",
            },
            "store": "user_variable",
            "behavior": "my_behavior",
        }
        action = HTTPRequestAction(items)
        behavior = self.user.descriptions["behaviors"]["my_behavior"]
        user_a = Mock(
            settings=make_settings_mock(),
            parametrizer=Mock(collect=lambda *args, **kwargs: {}),
            descriptions=self.user.descriptions,
        )
        user_b = Mock(
            settings=make_settings_mock(),
            parametrizer=Mock(collect=lambda *args, **kwargs: {}),
            descriptions=self.user.descriptions,
        )

        slow_context, slow_response = make_response_context(data={'data': 'value'})

        async def slow_json(*args, **kwargs):
            await asyncio.sleep(0.05)
            return {'data': 'value'}

        slow_response.json = slow_json
        request_mock.side_effect = [slow_context, make_timeout_context(0)]
        await asyncio.gather(action.run(user_a, None, {}), action.run(user_b, None, {}))

        # A: успех — success-метрика, данные записаны
        monitoring_mock.counter_req_out_success.assert_called_once_with("test_app", "isearch")
        user_a.variables.set.assert_called_once_with("user_variable", {'data': 'value'})
        # B: таймаут — error-метрика и timeout_action
        monitoring_mock.counter_req_out_error.assert_called_once_with("test_app", "isearch")
        self.assertTrue(behavior.timeout_action.run.called)
        user_b.variables.set.assert_not_called()

    @patch('smart_kit.action.http.monitoring')
    @patch('aiohttp.request')
    async def test_method_params_not_mutated_and_timeout_recomputed(self, request_mock, monitoring_mock):
        self.set_request_mock_attribute(request_mock, return_value={'data': 'value'})
        items = {
            "params": {
                "method": "POST",
                "url": "https://my.url.com",
                "integration_name": "isearch",
            },
            "store": "user_variable",
            "behavior": "my_behavior",
        }
        action = HTTPRequestAction(items)
        await action.run(self.user, None, {})
        self.assertNotIn("timeout", action.method_params)
        # повторный вызов того же экземпляра: таймаут пересчитывается, а не оборачивается повторно
        await action.run(self.user, None, {})
        self.assertEqual(request_mock.call_count, 2)
        self.assertEqual(request_mock.call_args_list[1].kwargs.get("timeout"), ClientTimeout(self.TIMEOUT))

    @patch('smart_kit.action.http.monitoring')
    @patch('aiohttp.request')
    async def test_content_type_error_returns_raw_content(self, request_mock, monitoring_mock):
        context, response = make_response_context(data=None)
        response.json = AsyncMock(side_effect=aiohttp.client_exceptions.ContentTypeError(
            request_info=None, history=()))
        response.content = Mock(read=AsyncMock(return_value=b"raw content"))
        request_mock.return_value = context
        items = {
            "params": {
                "method": "POST",
                "url": "https://my.url.com",
            },
            "store": "user_variable",
            "behavior": "my_behavior",
        }
        response_data, error = await HTTPRequestAction(items)._make_response({}, self.user)
        self.assertEqual(response_data, b"raw content")
        self.assertIsNone(error)
        self.assertTrue(response.content.read.called)

    def test_get_metric_app_name_never_raises(self):
        """Сбой определения имени приложения (не настроен app_config) не должен бросать в бизнес-вызов."""
        from unittest.mock import patch

        from smart_kit.action.http import get_metric_app_name

        user = Mock(settings=Mock(app_name=None))
        with patch("smart_kit.configs.get_app_config", side_effect=AttributeError("not configured")):
            self.assertEqual(get_metric_app_name(user), "unknown")

    @patch('smart_kit.action.http.monitoring')
    @patch('aiohttp.request')
    async def test_on_response_hook_exception_isolated(self, request_mock, monitoring_mock):
        """Исключение в хуке подкласса (например, при сохранении cookies) не должно ронять запрос."""
        context, _ = make_response_context(data={'data': 'value'})
        request_mock.return_value = context

        class BrokenHookAction(HTTPRequestAction):
            def _on_response(self, user, response):
                raise KeyError("boom")

        items = {
            "params": {"method": "POST", "url": "https://my.url.com"},
            "store": "user_variable",
            "behavior": "my_behavior",
        }
        await BrokenHookAction(items).run(self.user, None, {})
        self.user.variables.set.assert_called_with("user_variable", {'data': 'value'})
        monitoring_mock.counter_req_out_success.assert_called_once()

    @patch('aiohttp.request')
    async def test_cookie_action_saves_cookies_via_hook(self, request_mock):
        """Cookies сохраняются через хук _on_response, пока доступен живой response."""
        from http.cookies import SimpleCookie

        from smart_kit.action.http_with_cookie import HTTPRequestActionWithCookie

        context, response = make_response_context(data={'data': 'value'})
        response.cookies = SimpleCookie("session=abc")
        request_mock.return_value = context
        user = Mock(
            settings=make_settings_mock(template_settings={"ufs": {"back_cookie_whitelist": ["session"]}}),
            parametrizer=Mock(collect=lambda *args, **kwargs: {}),
            descriptions=self.user.descriptions,
        )
        user.private_vars.get.return_value = {}
        items = {
            "params": {"method": "POST", "url": "https://my.url.com"},
            "store": "user_variable",
            "behavior": "my_behavior",
        }
        await HTTPRequestActionWithCookie(items).run(user, None, {})
        user.private_vars.set.assert_called_once()

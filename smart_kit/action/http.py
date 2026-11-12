from __future__ import annotations

import asyncio
from typing import Any

import aiohttp
import aiohttp.client_exceptions
from aiohttp import ClientTimeout

import core.logging.logger_constants as log_const
from core.basic_models.actions.command import Command
from core.basic_models.actions.string_actions import NodeAction
from core.logging.logger_utils import log
from core.model.base_user import BaseUser
from core.monitoring.monitoring import monitoring
from core.text_preprocessing.base import BaseTextPreprocessingResult


def get_metric_app_name(user: BaseUser) -> str:
    """Имя приложения для метрик req_out_*: user.settings.app_name -> APP_NAME -> "unknown".

    У декоратора @monitoring.req_out нет user, поэтому там только APP_NAME.
    Не бросает исключений — сбой не должен ломать бизнес-вызов.
    """
    try:
        from smart_kit.configs import get_app_config
        settings = getattr(user, "settings", None)
        return getattr(settings, "app_name", None) or getattr(get_app_config(), "APP_NAME", None) or "unknown"
    except Exception:
        return "unknown"


class HTTPRequestAction(NodeAction):
    """
    Example:
        {
            "params": {
                "method": "POST",
                "url": "https://some_url.com/...",
                // опционально: имя интеграции для логов и метрик req_out_*.
                // Статичный идентификатор из конфигурации, рендерить из переменных нельзя.
                "integration_name": "some_integration",
                ... (см. BaseHttpRequestAction)
            },
            "store": "...",    // переменная user.variables для результата
            "behavior": "..."  // behavior, вызываемый после запроса
        }
    """

    POST = "POST"
    GET = "GET"
    PUT = "PUT"
    DELETE = "DELETE"
    PATCH = "PATCH"
    DEFAULT_METHOD = POST
    DEFAULT_TIMEOUT = 3

    TIMEOUT = "TIMEOUT"
    CONNECTION = "CONNECTION"

    def __init__(self, items: dict[str, Any], id: str | None = None):
        super().__init__(items, id)
        self.method_params = items["params"]
        self.method_params.setdefault("method", self.DEFAULT_METHOD)
        # integration_name забираем из method_params, чтобы он не улетел в параметры aiohttp.request
        name = self.method_params.pop("integration_name", None)
        self.integration_name = name or id or self.__class__.__name__
        if not name:
            log(f"{self.__class__.__name__} ({id}): integration_name is not set, "
                f"using \"%(integration_name)s\" for req_out_* metrics and logs",
                params={"integration_name": self.integration_name}, level="WARNING")
        self.init_save_params(items)

    def init_save_params(self, items):
        self.store = items.get("store")
        self.behavior = items.get("behavior")

    def _get_timeout(self, user: BaseUser) -> ClientTimeout:
        """Таймаут одной попытки: params -> behavior -> DEFAULT_TIMEOUT.

        Считается на каждый вызов: экземпляры действий общие, состояние в self недопустимо.
        """
        behavior_description = user.descriptions["behaviors"].get(self.behavior)
        timeout = self.method_params.get("timeout")
        if timeout is None:
            timeout = behavior_description.timeout(user) if behavior_description else self.DEFAULT_TIMEOUT
        return ClientTimeout(timeout)

    @staticmethod
    def _check_headers_validity(headers: dict[str, Any], user) -> dict[str, str]:
        for header_name, header_value in list(headers.items()):
            if not isinstance(header_value, (str, bytes)):
                if isinstance(header_value, (int, float, bool)):
                    headers[header_name] = str(header_value)
                else:
                    log(f"{__class__.__name__}._check_headers_validity remove header {header_name} because "
                        f"({type(header_value)}) is not in [int, float, bool, str, bytes]", user=user,
                        params={
                            log_const.KEY_NAME: "sent_http_remove_header",
                        })
                    del headers[header_name]
        return headers

    def _on_response(self, user, response):
        """Хук для подклассов: вызывается внутри контекст-менеджера, пока доступен response."""

    async def _perform_attempt(self, request_parameters: dict, user: BaseUser):
        """Одна попытка запроса: вызов, лог ответа, проверка статуса, парсинг тела."""
        async with aiohttp.request(**request_parameters) as response:
            try:
                self._on_response(user, response)
            except Exception:
                # сбой хука подкласса (например, сохранения cookies) не должен ронять запрос
                log(f"{self.__class__.__name__}._on_response failed", user=user,
                    params={log_const.KEY_NAME: "sent_http_request"}, level="ERROR", exc_info=True)
            # лог до raise_for_status: ошибочные статусы (например, 429) тоже видны в got_http_response
            self._log_response(user, response)
            response.raise_for_status()
            try:
                return await response.json()
            except aiohttp.client_exceptions.ContentTypeError:
                return await response.content.read()

    async def _make_response(self, request_parameters: dict, user: BaseUser) -> tuple[Any, str | None]:
        """Запрос -> (response, error). Ошибка не пишется в self: экземпляры общие,
        конкурентные run() могут перемешиваться на await'ах."""
        try:
            return await self._perform_attempt(request_parameters, user), None
        except (aiohttp.ServerTimeoutError, asyncio.TimeoutError):
            return None, self.TIMEOUT
        except aiohttp.ClientError:
            return None, self.CONNECTION

    def _get_request_params(self, user: BaseUser, text_preprocessing_result: BaseTextPreprocessingResult,
                            params: dict[str, str | float | int] | None = None):
        collected = user.parametrizer.collect(text_preprocessing_result)
        params.update(collected)
        request_parameters = self._get_rendered_tree_recursive(self._get_template_tree(self.method_params),
                                                               params)
        req_headers = request_parameters.get("headers")
        if req_headers:
            # Заголовки в запросах должны иметь тип str или bytes. Поэтому добавлена проверка и приведение к типу str,
            # на тот случай если в сценарии заголовок указали как int, float и тд
            request_parameters["headers"] = self._check_headers_validity(req_headers, user)
        request_parameters["timeout"] = self._get_timeout(user)
        return request_parameters

    def _log_request(self, user, request_parameters, additional_params=None):
        additional_params = additional_params or {}
        log(f"{self.__class__.__name__}.run sent https request ", user=user, params={
            **request_parameters,
            "integration_name": self.integration_name,
            log_const.KEY_NAME: "sent_http_request",
            **additional_params,
        })

    def _log_response(self, user, response, additional_params=None):
        additional_params = additional_params or {}
        log(f"{self.__class__.__name__}.run get https response ", user=user, params={
            'headers': dict(response.headers),
            'cookie': {k: v.value for k, v in response.cookies.items()},
            'status': response.status,
            "integration_name": self.integration_name,
            log_const.KEY_NAME: "got_http_response",
            **additional_params,
        })

    def _emit_req_out_metric(self, user, error):
        """Метрики 4, 6 из реестра: req_out_success / req_out_error с лейблом integration_name."""
        app_name = get_metric_app_name(user)
        if error is None:
            monitoring.counter_req_out_success(app_name, self.integration_name)
        else:
            monitoring.counter_req_out_error(app_name, self.integration_name)

    async def process_result(self, response, user, text_preprocessing_result, params, error=None):
        """Выбор ветки behavior по результату запроса. error передаётся явно, а не через self:
        экземпляры действий общие, подклассы могут вставить await до его чтения."""
        behavior_description = user.descriptions["behaviors"][self.behavior] if self.behavior else None
        action = None
        if error is None:
            user.variables.set(self.store, response)
            action = behavior_description.success_action if behavior_description else None
        elif behavior_description is not None:
            action = behavior_description.timeout_action if error == self.TIMEOUT \
                else behavior_description.fail_action
        if action:
            return await action.run(user, text_preprocessing_result, None)

    async def run(self, user: BaseUser, text_preprocessing_result: BaseTextPreprocessingResult,
                  params: dict[str, str | float | int] | None = None) -> list[Command] | None:
        params = params or {}
        request_parameters = self._get_request_params(user, text_preprocessing_result, params)
        self._log_request(user, request_parameters)
        response, error = await self._make_response(request_parameters, user)
        self._emit_req_out_metric(user, error)
        if response is not None:
            log("response data: %(body)s", user=user, params={"body": response,
                "integration_name": self.integration_name}, level="INFO")
        return await self.process_result(response, user, text_preprocessing_result, params, error)

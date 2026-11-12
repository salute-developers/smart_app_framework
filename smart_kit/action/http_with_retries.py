import asyncio

import aiohttp

import core.logging.logger_constants as log_const
from core.logging.logger_utils import log
from core.monitoring.monitoring import monitoring
from smart_kit.action.http import HTTPRequestAction, get_metric_app_name


class HTTPRequestActionWithRetries(HTTPRequestAction):
    """HTTPRequestAction с перезапросом (новый type "http_request_with_retries").

    Ретраятся сетевые ошибки (таймаут/обрыв) и статусы из http_request_retry_statuses.
    Остальное — как в базовом классе: TIMEOUT/CONNECTION и соответствующий action из behavior.

    Настройки в template_settings:
      http_request_max_attempts   — ОБЩЕЕ число попыток, по умолчанию 3;
      http_request_retry_statuses — статусы для перезапроса, по умолчанию [429];
      http_request_retry_delay    — пауза между попытками (сек), по умолчанию 0.

    Бюджет времени: max_attempts * timeout + суммарные delay, общего дедлайна нет.
    Retry-After не учитывается, бэк-офф фиксированный, без jitter.
    Каждая повторная попытка инкрементит метрику {app}_req_out_retry.

    Example:
        {
            "type": "http_request_with_retries",
            "params": {
                "integration_name": "isearch",
                "method": "POST",
                "url": "https://some_url.com/...",
                ...
            },
            "store": "...",    // переменная user.variables для результата
            "behavior": "..."  // behavior, вызываемый после запроса
        }
    """

    DEFAULT_MAX_ATTEMPTS = 3
    DEFAULT_RETRY_STATUSES = (429,)
    DEFAULT_RETRY_DELAY = 0

    @staticmethod
    def _get_template_settings(user) -> dict:
        settings = getattr(user, "settings", None)
        if settings is None:
            return {}
        try:
            return settings["template_settings"]
        except (KeyError, TypeError):
            return {}

    def _get_max_attempts(self, user) -> int:
        """Общее число попыток (минимум 1, чтобы запрос всегда выполнялся)."""
        value = self._get_template_settings(user).get("http_request_max_attempts", self.DEFAULT_MAX_ATTEMPTS)
        try:
            return max(1, int(value))
        except (TypeError, ValueError):
            log(f"{self.__class__.__name__}: invalid http_request_max_attempts value %(value)s, "
                f"using default %(default)s", user=user,
                params={"value": value, "default": self.DEFAULT_MAX_ATTEMPTS}, level="WARNING")
            return self.DEFAULT_MAX_ATTEMPTS

    def _get_retry_statuses(self, user) -> tuple:
        """HTTP-статусы для перезапроса; нормализуем к int ("429" из YAML -> 429)."""
        statuses = self._get_template_settings(user).get(
            "http_request_retry_statuses", self.DEFAULT_RETRY_STATUSES)
        # в YAML статус может быть задан и скаляром, и списком
        if not isinstance(statuses, (list, tuple, set, frozenset)):
            statuses = [statuses]
        normalized = []
        for status in statuses:
            try:
                normalized.append(int(status))
            except (TypeError, ValueError):
                log(f"{self.__class__.__name__}: invalid http_request_retry_statuses value %(value)s ignored",
                    user=user, params={"value": status}, level="WARNING")
        return tuple(normalized)

    def _get_retry_delay(self, user) -> float:
        """Пауза между попытками в секундах (по умолчанию 0)."""
        value = self._get_template_settings(user).get("http_request_retry_delay", self.DEFAULT_RETRY_DELAY)
        try:
            return max(0.0, float(value))
        except (TypeError, ValueError):
            return self.DEFAULT_RETRY_DELAY

    def _log_retry(self, user, reason, attempt: int, max_attempts: int):
        params = {
            "attempt": attempt,
            "max_attempts": max_attempts,
            "reason": reason,
            "integration_name": self.integration_name,
            log_const.KEY_NAME: "http_request_retry",
        }
        log(f"{self.__class__.__name__} retry http request: attempt %(attempt)s of %(max_attempts)s, "
            f"reason: %(reason)s", user=user, params=params)

    def _emit_retry_metric(self, user, reason):
        monitoring.counter_req_out_retry(get_metric_app_name(user), self.integration_name, reason)

    async def _make_response(self, request_parameters: dict, user) -> tuple:
        max_attempts = self._get_max_attempts(user)
        retry_statuses = self._get_retry_statuses(user)
        retry_delay = self._get_retry_delay(user)
        error = None
        for attempt in range(1, max_attempts + 1):
            retry_reason = None
            try:
                return await self._perform_attempt(request_parameters, user), None
            except aiohttp.ClientResponseError as e:
                if e.status in retry_statuses and attempt < max_attempts:
                    retry_reason = e.status
                else:
                    # вне списка ретраев или попытки исчерпаны — как в базовом классе:
                    # raise_for_status -> ClientError -> CONNECTION
                    error = self.CONNECTION
            except (aiohttp.ServerTimeoutError, asyncio.TimeoutError):
                error = self.TIMEOUT
                if attempt < max_attempts:
                    # на последней попытке ретрая уже не будет — не логируем и не считаем его
                    retry_reason = self.TIMEOUT
            except aiohttp.ClientError:
                # сетевые ошибки ретраим всегда
                error = self.CONNECTION
                if attempt < max_attempts:
                    retry_reason = self.CONNECTION
            if retry_reason is not None:
                self._log_retry(user, retry_reason, attempt, max_attempts)
                self._emit_retry_metric(user, retry_reason)
                if retry_delay > 0:
                    await asyncio.sleep(retry_delay)
                continue
            return None, error
        return None, error

from contextlib import asynccontextmanager
from unittest.mock import MagicMock, Mock, AsyncMock

import asyncio

import aiohttp


def make_settings_mock(app_name: str = "test_app", template_settings: dict | None = None) -> MagicMock:
    """Единый фейк user.settings: реальный Settings поддерживает __getitem__ (BaseConfig) и имеет атрибут app_name."""
    settings = MagicMock()
    settings.app_name = app_name
    settings.__getitem__.return_value = template_settings or {}
    return settings


@asynccontextmanager
async def make_timeout_context(delay: float = 0.02):
    """Эмулирует aiohttp.request, который падает таймаутом через delay секунд после входа в async with."""
    await asyncio.sleep(delay)
    raise aiohttp.ServerTimeoutError()
    yield  # pragma: no cover - недостижимо: исключение брошено раньше


def make_response_context(status=200, data=None):
    """Создаёт контекст-менеджер, который эмулирует `async with aiohttp.request(...) -> response`."""
    response = Mock(
        status=status,
        json=AsyncMock(return_value=data),
        cookies={},
        headers={},
    )
    if status >= 400:
        response.raise_for_status = Mock(
            side_effect=aiohttp.ClientResponseError(request_info=None, history=(), status=status, message="error"))
    else:
        response.raise_for_status = Mock()
    # __aexit__ должен возвращать False, чтобы исключения из тела пробрасывались, как в реальном aiohttp
    context = Mock(__aenter__=AsyncMock(return_value=response), __aexit__=AsyncMock(return_value=False))
    return context, response

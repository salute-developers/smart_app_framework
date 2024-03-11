"""
# Модель базового ответа.

От него должны быть отнаследованы все ответы.
"""
from typing import Any

from pydantic import BaseModel, Field

from nlpf_statemachine.models.debug_info import DebugInfo
from nlpf_statemachine.models.enums import IntegrationRequestType


class Response(BaseModel):
    """# Базовая модель ответа."""

    messageName: str
    """Наименование сообщения в кафку."""
    payload: Any = Field(description="Payload ответа.", default_factory=dict)
    """Payload ответа."""
    request_type: str = Field(description="Способ интеграции.", default=IntegrationRequestType.KAFKA)
    """Способ интеграции."""
    request_data: dict = Field(description="Конфигурация интеграции.", default_factory=dict)
    """Конфигурация интеграции."""
    debug_info: DebugInfo = Field(
        description="Отладочная информация для тестов, не возвращается в ответах.",
        default_factory=DebugInfo,
    )
    """Отладочная информация для тестов, не возвращается в ответах."""

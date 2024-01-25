"""
# Модель базового ответа.

От него должны быть отнаследованы все ответы.
"""
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field

from nlpf_statemachine.models.debug_info import DebugInfo
from nlpf_statemachine.models.enums import IntegrationRequestType


class Response(BaseModel):
    """# Базовая модель ответа."""

    messageName: str = Field(description="MessageName в кафку.")
    payload: Any = Field(description="Payload ответа.", default_factory=dict)
    request_type: Optional[str] = Field(description="Способ интеграции.", default=IntegrationRequestType.KAFKA)
    request_data: Optional[Dict] = Field(description="Конфигурация интеграции.", default_factory=dict)
    debug_info: DebugInfo = Field(
        description="Отладочная информация для тестов, не возвращается в ответах.",
        default_factory=DebugInfo,
    )

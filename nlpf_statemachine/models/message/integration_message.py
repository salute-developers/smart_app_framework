"""
# Базовые модели для интеграций.
"""

from typing import Optional, Dict

from pydantic import BaseModel, Field

from nlpf_statemachine.models.enums import Event
from .protocol import BaseMessage


class IntegrationPayload(BaseModel):
    """
    # Описание модели IntegrationPayload.
    """

    status: Optional[str] = Field(default=None)
    """Статус интеграции."""
    errorTitle: Optional[str] = Field(default=None)
    """Заголовок ошибки (если есть)."""
    errorMessage: Optional[str] = Field(default=None)
    """Сообщение об ошибке (если есть)."""
    error: Optional[str] = Field(default=None)
    """Информация об ошибке (если есть)."""
    data: Optional[Dict] = Field(default=None)
    """Данные, полученные в ответ от интеграции."""


class IntegrationMessage(BaseMessage):
    """
    # Описание модели IntegrationMessage.
    """

    payload: IntegrationPayload
    """Коллекция, в которой передается дополнительная информация."""


class LocalTimeout(BaseMessage):
    """
    # Описание модели LocalTimeout.

    Интеграция не ответила. Сработал Timeout.
    """

    messageName: str = Event.LOCAL_TIMEOUT
    """Тип запроса: LOCAL_TIMEOUT."""

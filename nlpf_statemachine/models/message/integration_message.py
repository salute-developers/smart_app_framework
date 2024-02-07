"""
# Базовые модели для интеграций.
"""

from pydantic import BaseModel, Field

from nlpf_statemachine.models.enums import Event
from .protocol import BaseMessage


class IntegrationPayload(BaseModel):
    """
    # Описание модели IntegrationPayload.
    """

    status: str | None = Field(default=None)
    """Статус интеграции."""
    errorTitle: str | None = Field(default=None)
    """Заголовок ошибки (если есть)."""
    errorMessage: str | None = Field(default=None)
    """Сообщение об ошибке (если есть)."""
    error: str | None = Field(default=None)
    """Информация об ошибке (если есть)."""
    data: dict | None = Field(default=None)
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

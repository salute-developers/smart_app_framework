"""
# Базовые модели для интеграций.
"""
from typing import Optional

from pydantic import BaseModel

from nlpf_statemachine.models.enums import Event

from .protocol import BaseMessage


class IntegrationPayload(BaseModel):
    """
    # Описание модели IntegrationPayload.
    """

    status: Optional[str]
    """Статус интеграции."""
    errorTitle: Optional[str]
    """Заголовок ошибки (если есть)."""
    errorMessage: Optional[str]
    """Сообщение об ошибке (если есть)."""
    error: Optional[str]
    """Информация об ошибке (если есть)."""
    data: Optional[dict]
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

"""
# Кастомные модели ответов.
"""
from typing import Optional
from pydantic import Field

from nlpf_statemachine.models.enums import IntegrationRequestType, ResponseMessageName
from nlpf_statemachine.models.message import RequestData
from .base_response import Response


class ErrorResponse(Response):
    """
    # Описание модели ErrorResponse.

    Модель ответа с ошибкой.
    """

    messageName: str = ResponseMessageName.ERROR
    """Наименование ответа."""


class IntegrationResponse(Response):
    """
    # Описание модели IntegrationResponse.

    Модель интеграционного ответа.
    """

    request_type: str = IntegrationRequestType.KAFKA
    """Способ интеграции."""
    request_data: Optional[RequestData] = Field(default_factory=RequestData)
    """Конфигурация интеграции."""


class NothingFound(Response):
    """
    # Описание модели NothingFound.

    Модель сообщения, что обработчика на голосовой запрос не найдено.
    """

    messageName: str = ResponseMessageName.NOTHING_FOUND
    """Наименование ответа."""


class DoNothing(Response):
    """
    # Описание модели DoNothing.

    Модель сообщения, что обработчика не найдено на конкретное событие, реагировать не надо.
    """

    messageName: str = ResponseMessageName.DO_NOTHING
    """Наименование ответа."""

"""
# Кастомные модели ответов.
"""
from typing import Dict, Optional

from pydantic import Field

from nlpf_statemachine.models.enums import IntegrationRequestType, ResponseMessageName
from nlpf_statemachine.models.message import RequestData

from .base_response import Response


class ErrorResponse(Response):
    """
    # Описание модели ErrorResponse.

    Модель ответа с ошибкой.
    """

    messageName: str = Field(description="Наименование ответа", default=ResponseMessageName.ERROR)


class IntegrationResponse(Response):
    """
    # Описание модели IntegrationResponse.

    Модель интеграционного ответа.
    """

    messageName: str = Field(description="Наименование ответа")
    request_type: str = Field(description="Способ интеграции", default=IntegrationRequestType.KAFKA)
    payload: Optional[Dict] = Field(description="Payload ответа")
    request_data: Optional[RequestData] = Field(description="Конфигурация интеграции.", default_factory=RequestData)


class NothingFound(Response):
    """
    # Описание модели NothingFound.

    Модель сообщения, что обработчика на голосовой запрос не найдено.
    """

    messageName: str = ResponseMessageName.NOTHING_FOUND


class DoNothing(Response):
    """
    # Описание модели DoNothing.

    Модель сообщения, что обработчика не найдено на конкретное событие, реагировать не надо.
    """

    messageName: str = ResponseMessageName.DO_NOTHING

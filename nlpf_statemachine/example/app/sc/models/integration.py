"""Описание моделей для интеграции."""
from typing import Optional

from pydantic import BaseModel

from nlpf_statemachine.example.app.sc.enums.integration_message_names import (
    IntegrationRequestMessageName, IntegrationResponseMessageName,
)
from nlpf_statemachine.models import UUID, BaseMessage, IntegrationPayload, IntegrationResponse


class GetDataPayload(BaseModel):
    """Payload для запроса данных."""

    uuid: UUID
    """UUID текущего запроса."""

    project: str
    """Текущий project."""


class GetDataRequest(IntegrationResponse):
    """Описание запроса получения данных."""

    messageName: str = IntegrationRequestMessageName.GENERATE_DATA
    """messageName запроса."""

    payload: GetDataPayload
    """payload запроса."""


class GetDataResponseData(BaseModel):
    """Основная часть ответа от интеграции."""

    data: str
    """Данные."""


class GetDataResponsePayload(IntegrationPayload):
    """Описание payload ответа от интеграции."""

    data: Optional[GetDataResponseData]
    """Данные."""


class GetDataResponse(BaseMessage):
    """Описание ответа от интеграции."""

    messageName: str = IntegrationResponseMessageName.GENERATE_DATA
    """Наименование (тип) запроса."""

    payload: GetDataResponsePayload
    """payload ответа."""

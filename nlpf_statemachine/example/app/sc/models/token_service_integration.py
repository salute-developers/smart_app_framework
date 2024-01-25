"""Описание моделей для интеграции с Токен-Сервисом."""
from typing import Optional

from pydantic import BaseModel

from nlpf_statemachine.example.app.sc.enums.integration_message_names import (
    IntegrationRequestMessageName, IntegrationResponseMessageName,
)
from nlpf_statemachine.models import UUID, BaseMessage, IntegrationPayload, IntegrationResponse


class GetTokenPayload(BaseModel):
    """Payload для запроса токена."""

    uuid: UUID
    """UUID текущего запроса."""

    projectId: str
    """Текущий projectId."""


class GetTokenRequest(IntegrationResponse):
    """Описание запроса получения токена."""

    messageName: str = IntegrationRequestMessageName.GENERATE_TOKEN
    """messageName запроса."""

    payload: GetTokenPayload
    """payload запроса."""


# ==== Token Service Response ====
class GetTokenResponseData(BaseModel):
    """Основная часть ответа от токен сервиса, в которой лежит сам токен."""

    accessToken: str
    """Токен."""

    expiresIn: str
    """Время жизни токена (timestamp протухания)."""


class GetTokenResponsePayload(IntegrationPayload):
    """Описание payload ответа от токен-сервиса."""

    data: Optional[GetTokenResponseData]
    """Данные."""


class GetTokenResponse(BaseMessage):
    """Описание ответа от токен-сервиса."""

    messageName: str = IntegrationResponseMessageName.GENERATE_TOKEN
    """Наименование (тип) запроса."""

    payload: GetTokenResponsePayload
    """payload ответа."""

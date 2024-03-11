"""
# Запуск других аппов.
"""
from pydantic import BaseModel, Field

from nlpf_statemachine.models.enums import ResponseMessageName
from nlpf_statemachine.models.message import AppInfo, ServerAction
from .base_response import Response


class PolicyRunAppServerAction(ServerAction):
    """
    # Описание модели PolicyRunAppServerAction.
    """

    action_id: str = Field(default="run_app")
    """
    Действие, которое обрабатывает бэкенд смартапа.
    Значение по умолчанию для запуска: *run_app*.
    """
    app_info: AppInfo
    """Информация о смартапе."""


class PolicyRunAppPayload(BaseModel):
    """
    # Описание модели PolicyRunAppPayload.
    """

    server_action: PolicyRunAppServerAction
    """MessageName запроса."""


class PolicyRunApp(Response):
    """
    # Описание модели PolicyRunApp.
    """

    messageName: str = ResponseMessageName.POLICY_RUN_APP
    """MessageName запроса."""
    payload: PolicyRunAppPayload = Field(default_factory=PolicyRunAppPayload)
    """Payload ответа."""

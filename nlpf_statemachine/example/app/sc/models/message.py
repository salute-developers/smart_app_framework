"""
# Описание моделей запросов.
"""
from typing import Optional

from pydantic import BaseModel, Field

from nlpf_statemachine.models import (
    AssistantMeta,
    CurrentApp,
    MessageToSkill,
    MessageToSkillPayload,
    ServerActionMessage,
    ServerActionPayload,
)


class CustomState(BaseModel):
    """
    # Описание стейта с фронта.
    """

    replace_message: Optional[bool] = Field(default=None)
    """Флаг подмены сообщения для примера с pre_process."""

    screen: Optional[str] = Field(default=None)
    """Наименование текущего экрана."""


class CustomCurrentApp(CurrentApp):
    """
    # Текущий current_app в запросе.
    """

    state: Optional[CustomState] = Field(default=None)
    """Описание стейта."""


class CustomMeta(AssistantMeta):
    """
    # Модель meta в запросе.
    """

    current_app: Optional[CustomCurrentApp] = Field(default=None)
    """Текущий current_app."""


class CustomAssistantPayloadMessageToSkill(MessageToSkillPayload):
    """
    # Описание Payload для текущего аппа для сообщения MessageToSkill.
    """

    meta: CustomMeta = Field(default_factory=CustomMeta)
    """Текущий meta."""


class CustomAssistantPayloadServerAction(ServerActionPayload):
    """
    # Описание Payload для текущего аппа для сообщения ServerAction.
    """

    meta: CustomMeta = Field(default_factory=CustomMeta)
    """Текущий meta."""


class CustomMessageToSkill(MessageToSkill):
    """
    # Описание запроса MessageToSkill для текущего аппа.
    """

    payload: CustomAssistantPayloadMessageToSkill
    """Описание Payload."""


class CustomAssistantMessageServerAction(ServerActionMessage):
    """
    # Описание запроса ServerAction для текущего аппа.
    """

    payload: CustomAssistantPayloadServerAction
    """Описание Payload."""

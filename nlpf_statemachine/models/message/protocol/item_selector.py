"""
# Описание ItemSelector.
"""
from typing import Any

from pydantic import BaseModel, Field


class AssistantViewAction(BaseModel):
    """
    # Описание модели AssistantViewAction.

    Описания события, которое ожидается к возвращению в веб-приложение.
    """

    type: str | None = Field(default=None)
    """Уникальный тип/id действия для обработки в веб-приложении."""
    payload: Any | None = Field(default=None)
    """Данные от бэкенда без изменений."""


class AssistantVoiceAction(BaseModel):
    """
    # Описание модели AssistantVoiceAction.

    Основные события, которые можно вызвать голосом (= UI-элементы).
    """

    number: int | None = Field(default=None)
    """Порядковый номер элемента."""
    id: str | None = Field(default=None)
    """Уникальный id элемента."""
    title: str | None = Field(default=None)
    """Ключевая фраза, которая должна приводить к данному действию."""
    type: str | None = Field(default=None)
    """Тип элемента."""
    paraphrases: list[str] | None = Field(default=None)
    """Фразы-синонимы, которые должны быть расценены как данное действие."""
    payload: dict | None = Field(default=None)
    """Дополнительные данные для бэкенда."""
    action: AssistantViewAction | None = Field(default=None)
    """Объект, который ожидается к возвращению в веб-приложение."""


class ItemSelector(BaseModel):
    """
    # Описание модели ItemSelector.

    Множество объектов, которые можно вызвать голосом.
    """

    items: list[AssistantVoiceAction] | None = Field(default=None)
    """Список элементов."""

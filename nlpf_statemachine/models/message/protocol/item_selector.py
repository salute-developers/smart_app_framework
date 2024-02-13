"""
# Описание ItemSelector.
"""
from typing import Any, Optional, List, Dict

from pydantic import BaseModel, Field


class AssistantViewAction(BaseModel):
    """
    # Описание модели AssistantViewAction.

    Описания события, которое ожидается к возвращению в веб-приложение.
    """

    type: Optional[str] = Field(default=None)
    """Уникальный тип/id действия для обработки в веб-приложении."""
    payload: Optional[Any] = Field(default=None)
    """Данные от бэкенда без изменений."""


class AssistantVoiceAction(BaseModel):
    """
    # Описание модели AssistantVoiceAction.

    Основные события, которые можно вызвать голосом (= UI-элементы).
    """

    number: Optional[int] = Field(default=None)
    """Порядковый номер элемента."""
    id: Optional[str] = Field(default=None)
    """Уникальный id элемента."""
    title: Optional[str] = Field(default=None)
    """Ключевая фраза, которая должна приводить к данному действию."""
    type: Optional[str] = Field(default=None)
    """Тип элемента."""
    paraphrases: Optional[List[str]] = Field(default=None)
    """Фразы-синонимы, которые должны быть расценены как данное действие."""
    payload: Optional[Dict] = Field(default=None)
    """Дополнительные данные для бэкенда."""
    action: Optional[AssistantViewAction] = Field(default=None)
    """Объект, который ожидается к возвращению в веб-приложение."""


class ItemSelector(BaseModel):
    """
    # Описание модели ItemSelector.

    Множество объектов, которые можно вызвать голосом.
    """

    items: Optional[List[AssistantVoiceAction]] = Field(default=None)
    """Список элементов."""

"""
# Описание ItemSelector.
"""
from typing import Any, Dict, List, Optional

from pydantic import BaseModel


class AssistantViewAction(BaseModel):
    """
    # Описание модели AssistantViewAction.

    Описания события, которое ожидается к возвращению в веб-приложение.
    """

    type: Optional[str]
    """Уникальный тип/id действия для обработки в веб-приложении."""
    payload: Optional[Any]
    """Данные от бэкенда без изменений."""


class AssistantVoiceAction(BaseModel):
    """
    # Описание модели AssistantVoiceAction.

    Основные события, которые можно вызвать голосом (= UI-элементы).
    """

    number: Optional[int]
    """Порядковый номер элемента."""
    id: Optional[str]
    """Уникальный id элемента."""
    title: Optional[str]
    """Ключевая фраза, которая должна приводить к данному действию."""
    type: Optional[str]
    """Тип элемента."""
    paraphrases: Optional[List[str]]
    """Фразы-синонимы, которые должны быть расценены как данное действие."""
    payload: Optional[Dict]
    """Дополнительные данные для бэкенда."""
    action: Optional[AssistantViewAction]
    """Объект, который ожидается к возвращению в веб-приложение."""


class ItemSelector(BaseModel):
    """
    # Описание модели ItemSelector.

    Множество объектов, которые можно вызвать голосом.
    """

    items: List[AssistantVoiceAction]
    """Список элементов."""

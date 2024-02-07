"""
# Описание моделей для StaticStorage.
"""

from pydantic import BaseModel, Field

from .response import AssistantResponsePayload


class AssistantAnswer(AssistantResponsePayload):
    """
    # Описание модели AssistantAnswer.
    """

    answers: list[AssistantResponsePayload]
    """Список ответов."""


class StaticStorageItem(AssistantResponsePayload):
    """
    # Описание модели StaticStorageItem.
    """

    joy: AssistantAnswer | None = Field(default=None)
    """Ответы Джой."""
    sber: AssistantAnswer | None = Field(default=None)
    """Ответы Сбера."""
    athena: AssistantAnswer | None = Field(default=None)
    """Ответы Афины."""
    any: AssistantAnswer | None = Field(default=None)
    """Дефолтные ответы."""


class StaticStorage(BaseModel):
    """
    # Описание модели StaticStorage.
    """

    data: dict[str, StaticStorageItem] = Field(default_factory=dict)
    """Словарь ответов ассистентов."""

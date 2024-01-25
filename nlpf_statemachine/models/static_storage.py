"""
# Описание моделей для StaticStorage.
"""
from typing import Dict, List, Optional

from pydantic import BaseModel, Field

from .response import AssistantResponsePayload


class AssistantAnswer(AssistantResponsePayload):
    """
    # Описание модели AssistantAnswer.
    """

    answers: List[AssistantResponsePayload]


class StaticStorageItem(AssistantResponsePayload):
    """
    # Описание модели StaticStorageItem.
    """

    joy: Optional[AssistantAnswer]
    sber: Optional[AssistantAnswer]
    athena: Optional[AssistantAnswer]
    any: Optional[AssistantAnswer]


class StaticStorage(BaseModel):
    """
    # Описание модели StaticStorage.
    """

    data: Dict[str, StaticStorageItem] = Field(default_factory=dict)

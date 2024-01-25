"""
# Описание модели ассистента.
"""
from typing import Optional

from pydantic import BaseModel

from nlpf_statemachine.models.enums import AssistantAppeal, AssistantGender, AssistantId, AssistantName


class Character(BaseModel):
    """
    # Модель ассистента.
    """

    id: Optional[AssistantId]
    name: Optional[AssistantName]
    gender: Optional[AssistantGender]
    appeal: Optional[AssistantAppeal]

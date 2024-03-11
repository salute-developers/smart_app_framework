"""
# Описание модели ассистента.
"""

from typing import Optional

from pydantic import BaseModel, Field

from nlpf_statemachine.models.enums import AssistantAppeal, AssistantGender, AssistantId, AssistantName


class Character(BaseModel):
    """
    # Модель ассистента.
    """

    id: Optional[AssistantId] = Field(default=None)
    name: Optional[AssistantName] = Field(default=None)
    gender: Optional[AssistantGender] = Field(default=None)
    appeal: Optional[AssistantAppeal] = Field(default=None)

"""
# Описание модели ассистента.
"""

from pydantic import BaseModel, Field

from nlpf_statemachine.models.enums import AssistantAppeal, AssistantGender, AssistantId, AssistantName


class Character(BaseModel):
    """
    # Модель ассистента.
    """

    id: AssistantId | None = Field(default=None)
    name: AssistantName | None = Field(default=None)
    gender: AssistantGender | None = Field(default=None)
    appeal: AssistantAppeal | None = Field(default=None)

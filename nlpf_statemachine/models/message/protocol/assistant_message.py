"""
Описание базового запроса в приложение с фронта.
"""
from pydantic import Field

from .base_message import BaseMessage
from .payload import AssistantPayload


class AssistantMessage(BaseMessage):
    """
    # Описание модели AssistantMessage.
    """

    payload: AssistantPayload = Field(default_factory=AssistantPayload)
    """
    Каждое сообщение содержит объект payload, наполнение которого зависит от типа сообщения.
    В будущем payload может быть дополнен новыми полями.
    """

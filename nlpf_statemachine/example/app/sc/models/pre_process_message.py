"""
# Описание моделей примера для пре и пост процессов.
"""
from nlpf_statemachine.example.app.sc.models.message import CustomMessageToSkill
from nlpf_statemachine.models import AssistantPayload, MessageToSkill


class CustomPreProcessMessagePayload(AssistantPayload):
    """
    # Payload для примеры работа пре-процесса.

    В `incoming_message` будет лежать весь пришедший запрос.
    """

    incoming_message: CustomMessageToSkill
    """Пришедший запрос."""


class CustomPreProcessMessage(MessageToSkill):
    """
    # Кастомное сообщения для примеры работа пре-процесса.

    В `payload.incoming_message` будет лежать весь пришедший запрос.
    """

    messageName: str = "CustomPreProcessMessage"
    """Тип сообщения. Определяет логику обработки события."""

    payload: CustomPreProcessMessagePayload
    """Описание Payload."""

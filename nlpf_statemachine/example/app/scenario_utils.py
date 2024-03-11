"""
# Общие для разных сценариев функции
"""

from nlpf_statemachine.example.app.sc.models.integration import GetDataPayload, GetDataRequest
from nlpf_statemachine.example.const import INTEGRATION_TOPIC_KEY
from nlpf_statemachine.models import AssistantMessage


def get_integration_data(message: AssistantMessage) -> GetDataRequest:
    """
    # Метод для генерации запроса в интеграцию.

    Args:
        message (AssistantMessage): Запрос от ассистента

    Returns:
        GetDataRequest: Запрос в интеграцию.
    """
    return GetDataRequest(
        payload=GetDataPayload(
            uuid=message.uuid,
            project=message.payload.app_info.projectId,
        ),
        request_data={
            "topic_key": INTEGRATION_TOPIC_KEY,
        },
    )

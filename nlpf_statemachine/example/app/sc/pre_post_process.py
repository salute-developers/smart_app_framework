"""
# Pre и Post процессы.
"""
from typing import Optional

from core.logging.logger_utils import behaviour_log
from nlpf_statemachine.example.app.sc.commands import generate_item
from nlpf_statemachine.example.app.sc.models.commands import InitCommand
from nlpf_statemachine.example.app.sc.models.context import ExampleContext
from nlpf_statemachine.example.app.sc.models.message import CustomMessageToSkill, CustomState
from nlpf_statemachine.example.app.sc.models.pre_process_message import (
    CustomPreProcessMessage, CustomPreProcessMessagePayload,
)
from nlpf_statemachine.models import AnswerToUser, AssistantMessage, Response


def pre_process(message: CustomMessageToSkill, state: CustomState) -> Optional[AssistantMessage]:
    """
    ## Pre-процесс.

    --- процесс в начале транзакции.

    В качестве примера проделаем следующий трюк: если в стейте прилетает флаг `replace_message`, то сгенерируем
    новое сообщение, где в payload будет лежать всё сообщение.

    Args:
        message (CustomMessageToSkill): пришедшее сообщение;
        state (CustomState): State из запроса;

    Returns:
        AssistantMessage: изменённое сообщение. (опционально!)
    """
    if state and state.replace_message:
        return CustomPreProcessMessage(
            payload=CustomPreProcessMessagePayload(
                incoming_message=message,
            ),
        )


def post_process(message: AssistantMessage, response: AnswerToUser, context: ExampleContext) -> Optional[Response]:
    """
    ## Post-процесс.

    --- процесс при завершении транзакции.

    Args:
        message (AssistantMessage): пришедшее сообщение;
        response (AnswerToUser): полученный ответ;
        context (ExampleContext): контекст;

    Returns:
        Response: изменённый ответ. (опционально!)
    """
    try:
        new_session = message.payload.new_session
    except Exception:
        new_session = False

    if new_session:
        if context.local.data:
            items = [
                generate_item(
                    smart_app_data=InitCommand(
                        data=context.local.data.data,
                    )),
            ]

            response.payload.items = items + response.payload.items
        else:
            behaviour_log("No token in context.", level="ERROR", params={"message_id": message.messageId})
            raise ValueError("No token")

    return response

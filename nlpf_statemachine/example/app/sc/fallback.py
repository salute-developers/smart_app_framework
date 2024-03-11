"""
# Обработка глобального фоллбека.
"""
from nlpf_statemachine.models import AnswerToUser, AssistantResponsePayload, BaseMessage


def fallback(message: BaseMessage) -> AnswerToUser:
    """## Обработка глобального фоллбека."""
    try:
        new_session = message.payload.new_session
    except Exception:
        new_session = False

    if new_session:
        payload = AssistantResponsePayload(
            pronounceText="Добро пожаловать в NLPF StateMachine :)",
        )
    else:
        payload = AssistantResponsePayload(
            pronounceText="Кажется, я что-то не уловил. Повторите, пожалуйста, свою мысль.",
        )
    return AnswerToUser(payload=payload)

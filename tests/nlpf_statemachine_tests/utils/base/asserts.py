"""
# Локальные утилиты для тестов.
"""
from unittest.mock import MagicMock
from pydantic import BaseModel

from nlpf_statemachine.models import BaseMessage, Context, Response


def assert_action_call(
        action: MagicMock,
        response: Response,
        message: BaseMessage,
        context: Context,
        form: dict,
) -> None:
    """
    ## Проверка на вызов экшена.

    Args:
        action: вызываемый экшен;
        response: полученный ответ;
        message: сообщение, которое ушло в ContextManager;
        context: контекст;
        form: форма;

    Returns:
        None.
    """
    # action.assert_called_with(message=message, context=context, form=form)
    if isinstance(action.return_value.payload, BaseModel):
        payload = action.return_value.payload.model_dump()
    else:
        payload = action.return_value.payload
    assert response.messageName == action.return_value.messageName
    if isinstance(response.payload, dict):
        assert response.payload == payload
    else:
        assert response.payload.model_dump() == payload

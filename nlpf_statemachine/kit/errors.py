"""
# Набор исключений для NLPF StateMachine.
"""
from typing import Any


class BaseActionError(Exception):
    """
    # Базовый Exception для экшенов.
    """

    def __init__(self, action: str) -> None:
        self.action = action


class ActionWithNoAnswerError(BaseActionError):
    """
    # Exception для экшена без ответа.
    """


class ActionWithNoValidAnswerError(BaseActionError):
    """
    # Exception для экшена с невалидным ответом.
    """

    def __init__(self, action: str, response: Any) -> None:
        super(ActionWithNoValidAnswerError, self).__init__(action=action)
        self.response = response


class ActionDisabledError(BaseActionError):
    """
    # Exception для отключённого экшена.
    """

"""
# Локальные утилиты для тестов.
"""
from typing import Any, Optional, Union
from unittest.mock import MagicMock

from pydantic import BaseModel

from nlpf_statemachine.models import AssistantResponsePayload, IntegrationResponse, IntegrationRequestType, Response
from tests.nlpf_statemachine_tests.utils import random_string


def action_mock(
        message_name: Optional[str] = None,
        payload: Optional[dict or BaseModel] = None,
        side_effect: Any = None,
) -> MagicMock:
    """
    ## Генерация экшена.

    Args:
        message_name (str, optional): Тип запроса;
        payload (dict, optional): Коллекция, в которой передается дополнительная информация.
        side_effect: Фоновый процесс при вызове экшена.

    Returns:
        MagicMock: мок экшена.
    """
    action = MagicMock(side_effect=side_effect)

    if not message_name:
        message_name = random_string()
    action.event = random_string()
    action.return_value = Response(
        messageName=message_name,
        payload=payload if payload else AssistantResponsePayload(),
    )
    action.__code__ = MagicMock()
    action.__code__.co_varnames = ["message", "context", "form"]
    action.__code__.co_argcount = 3
    return action


def action_with_exception_mock(exception: Optional[Exception] = None) -> MagicMock:
    """
    ## Генерация экшена с ошибкой.

    Args:
        exception (Exception, optional): Исключение, которое должно быть выброшено.

    Returns:
        MagicMock: мок экшена с ошибкой.
    """

    def function(*args, **kwargs) -> None:
        """
        ## Функция, которая выбрасывает ошибку.
        """
        if exception:
            raise exception
        raise Exception("Test Exception")

    action = action_mock(side_effect=function)
    return action


def action_integration_mock(
        message_name: Optional[str] = None,
        payload: Optional[Union[dict, BaseModel]] = None,
        request_data: Optional[dict] = None,
        request_type: str = IntegrationRequestType.KAFKA,
) -> MagicMock:
    """
    ## Мок интеграционного экшена.

    Args:
        message_name (str, optional): Тип запроса;
        payload (dict, optional): Коллекция, в которой передается дополнительная информация.
        request_data (dict, optional): данные для интеграции;
        request_type (str, optional): тип интеграции;

    Returns:
        MagicMock: мок интеграционного экшена.
    """
    action = action_mock()
    action.event = random_string()
    action.response_message_name = message_name or random_string()
    action.response_payload = payload if payload else {}
    action.request_data = request_data if request_data else {}
    action.request_type = request_type if request_type else {}
    action.return_value = IntegrationResponse(
        messageName=action.response_message_name,
        payload=action.response_payload,
        request_type=action.request_type,
        request_data=action.request_data,
    )
    return action

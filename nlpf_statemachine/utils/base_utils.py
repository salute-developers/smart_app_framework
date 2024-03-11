"""
# Утилиты, используемые под капотом в NLPF StateMachine.
"""
from typing import Any, Callable, Dict, Optional, Type

from nlpf_statemachine.models import AssistantMessage, AssistantState, BaseMessage, ServerActionMessage


def _get_state(message: BaseMessage) -> Optional[AssistantState]:
    try:
        return message.payload.meta.current_app.state
    except AttributeError:
        pass


def get_field_class(base_obj: Any, field: str) -> Type:
    """
    ## Определение типа поля у объекта.

    Args:
        base_obj: объект;
        field: наименование поля;

    Returns:
        Type: тип поля.
    """
    try:
        return base_obj.model_fields.get(field).annotation
    except Exception as e:
        print(e)


def get_kwargs(
        function: Callable,
        message: BaseMessage,
        **kwargs,
) -> Dict[str, Any]:
    """
    ## Получение аргументов, которые требует функция.

    Args:
        function (Callable): Функция, для которой необходимо достать параметры;
        message (nlpf_statemachine.models.message.message.MessageToSkill): Тело запроса.

    Returns:
        Dict[str, Any]: Параметры для функции.
    """
    func_kwargs = {}
    args = function.__code__.co_varnames[:function.__code__.co_argcount]
    arg_values = {
        "message": message,
        "payload": message.payload,
        "app_info": message.payload.app_info if isinstance(message, AssistantMessage) else None,
        "state": _get_state(message=message) if isinstance(message, AssistantMessage) else None,
        "server_action": message.payload.server_action if isinstance(message, ServerActionMessage) else None,
    }
    arg_values.update(kwargs)

    for arg_name in args:
        if arg_name in arg_values:
            func_kwargs[arg_name] = arg_values[arg_name]
        else:
            func_kwargs[arg_name] = None

    return func_kwargs

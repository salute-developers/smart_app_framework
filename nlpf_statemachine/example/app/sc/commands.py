"""
# Генераторы команд.
"""
from typing import Dict, Union

from nlpf_statemachine.models import AssistantCommand, CanvasAppItem, SmartAppDataCommand
from .models.commands import CustomCommand


def generate_item(smart_app_data: Union[AssistantCommand, Dict]) -> CanvasAppItem:
    """
    ## Генерация item-команды для списка items в ответе.

    Args:
        smart_app_data (AssistantCommand): Команда для фронта;

    Returns:
        CanvasAppItem: Элемент списка items в ответе.
    """
    return CanvasAppItem(
        command=SmartAppDataCommand(
            smart_app_data=smart_app_data,
        ),
    )


def custom_command(field_1: str, field_2: int) -> CanvasAppItem:
    """
    # Пример генерации кастомной команды c 2 полями.

    Args:
        field_1 (str): параметр 1 - строка;
        field_2: параметр 2 - число;

    Returns:
        CanvasAppItem: Элемент списка items в ответе с данной командой.
    """
    return generate_item(smart_app_data=CustomCommand(field_1=field_1, field_2=field_2))

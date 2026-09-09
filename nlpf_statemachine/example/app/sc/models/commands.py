"""
# Описание моделей для CanvasApp.
"""
from __future__ import annotations

from nlpf_statemachine.models import AssistantCommand

EXAMPLE_COMMAND_NAME = "EXAMPLE_COMMAND_NAME"


class InitCommand(AssistantCommand):
    """
    # Описание инициализационной команды.
    """

    command: str = "INIT"
    """Наименование команды."""
    data: str
    """data."""


class CustomCommand(AssistantCommand):
    """
    # Описание кастомной команды.

    Данная команда будет лежать в smart_app_data для фронта.
    """

    command: str = EXAMPLE_COMMAND_NAME
    """Наименование команды"""
    field_1: str
    """Параметр 1 типа str"""
    field_2: int
    """Параметр 2 типа int"""


class FormCommand(AssistantCommand):
    """
    # Описание кастомной команды.
    """

    command: str = "COMMAND"
    """Наименование команды."""
    custom_approve: str | None = None
    """Параметр custom_approve."""
    nlpf_approve: bool | None = None
    """Параметр nlpf_approve."""

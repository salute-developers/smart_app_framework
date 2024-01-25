"""
# Формы.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, Union

from core.logging.logger_utils import behaviour_log
from core.text_preprocessing.preprocessing_result import TextPreprocessingResult
from nlpf_statemachine.models import Context, MessageToSkill
from nlpf_statemachine.override.user import SMUser
from scenarios.scenario_models.field.field_filler_description import FieldFillerDescription


class Filler(ABC):
    """
    # Интерфейс для создания собственных филлеров для заполнения слотов.
    """

    @abstractmethod
    def run(self, message: MessageToSkill, context: Context) -> Any:
        """
        # Запуск филлера.

        *Основной метод для переопределения*.

        Args:
            message (nlpf_statemachine.models.message.protocol.assistant_message.MessageToSkill): Тело запроса.
            context (nlpf_statemachine.models.context.Context): Контекст.

        Returns:
            Any: то, что будет извлечено из запроса.
        """


class Form:
    """
    # Форма.

    Данный объект используется для описания формы в design-time.
    """

    def __init__(self) -> None:
        self._field_fillers = {}
        self._field_fillers_legacy = {}

    def extend(self, form: Form) -> None:
        """
        # Расширение формы другой формой.

        Args:
            form (Form): форма, поля которой будут добавлены в текущую.

        Returns:
            None.
        """
        self._field_fillers_legacy.update(form._field_fillers_legacy)
        self._field_fillers.update(form._field_fillers)

    def add_field(self, name: str, filler: Union[Filler, FieldFillerDescription]) -> None:
        """
        # Добавление слота на форму.

        Args:
            name (str): наименование слота;
            filler (Filler or FieldFillerDescription): объект филлер;

        Returns:
            None.
        """
        if name in self._field_fillers or name in self._field_fillers_legacy:
            behaviour_log(f"Field {name} already exists on form.", level="WARNING")

        if isinstance(filler, FieldFillerDescription):
            self._field_fillers_legacy[name] = filler

        if isinstance(filler, Filler):
            self._field_fillers[name] = filler

    def fill(self, message: MessageToSkill, context: Context,
             text_preprocessing_result: TextPreprocessingResult, user: SMUser) -> Dict[str, Any]:
        """
        # Заполнение формы в runtime.

        Args:
            message (nlpf_statemachine.models.message.protocol.assistant_message.MessageToSkill): Тело запроса.
            context (nlpf_statemachine.models.context.Context): Контекст.
            text_preprocessing_result (TextPreprocessingResult): NLPF TextPreprocessingResult.
            user (SMUser): NLPF User.

        Returns:
            Dict[str, Any]
        """
        fields = {}
        for name, filler in self._field_fillers_legacy.items():
            if isinstance(filler, FieldFillerDescription):
                try:
                    fields[name] = filler.extract(text_preprocessing_result, user)
                except Exception as exception:
                    behaviour_log(
                        f"Form filling got exception on field: {name}. Exception: {exception}.", level="ERROR",
                        exc_info=True, user=user,
                    )

        for name, filler in self._field_fillers.items():
            if isinstance(filler, Filler):
                try:
                    fields[name] = filler.run(message, context)
                except Exception as exception:
                    behaviour_log(
                        f"Form filling got exception on field: {name}. Exception: {exception}.", level="ERROR",
                        exc_info=True, user=user,
                    )

        return fields

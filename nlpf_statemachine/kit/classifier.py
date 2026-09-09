"""
# Классификаторы.
"""

from __future__ import annotations

import yaml

from core.logging.logger_utils import behaviour_log
from core.text_preprocessing.preprocessing_result import TextPreprocessingResult
from nlpf_statemachine.models import Context, MessageToSkill
from nlpf_statemachine.override.user import SMUser
from scenarios.scenario_models.field.field_filler_description import IntersectionFieldFiller


class Classifier:
    """
    # Базовый интерфейс для классификатора.
    """

    def __init__(self, id: str | None = None, screen: str | None = None) -> None:
        self.id = id
        self.screen = screen

    def run(self, message: MessageToSkill, context: Context, form: dict) -> str | None:
        """
        ## Запуск классификации.

        *Основной метод для переопределения*.

        Args:
            message (nlpf_statemachine.models.message.protocol.assistant_message.BaseMessage): Тело запроса.
            context (nlpf_statemachine.models.context.Context): Контекст.
            form (dict[str, Any]): Форма

        Returns:
            str: результат классификации (event).
        """
        return None

    def run_legacy(
            self, message: MessageToSkill,
            context: Context,
            form: dict,
            text_preprocessing_result: TextPreprocessingResult,
            user: SMUser,
    ) -> str | None:
        """
        ## Запуск классификации с использованием NLPF объектов.

        Args:
            message (nlpf_statemachine.models.message.protocol.assistant_message.BaseMessage): Тело запроса.
            context (nlpf_statemachine.models.context.Context): Контекст.
            form (dict[str, Any]): Форма.
            text_preprocessing_result (TextPreprocessingResult): NLPF TextPreprocessingResult.
            user (SMUser): NLPF User.

        Returns:
            str: результат классификации (event).
        """
        return None


class IntersectionClassifier(Classifier):
    """
    # Классификатор на основе простых вхождений слов во фразы.
    """

    def __init__(self, filename: str, screen: str | None = None, default: str | None = None) -> None:
        super().__init__(id="IntersectionClassifier", screen=screen)
        if filename:
            with open(filename) as file:
                cases = yaml.safe_load(file)
        else:
            cases = {}
        self.filler = IntersectionFieldFiller({"cases": cases, "default": default})
        behaviour_log(f"Classifier {self.id} of {len(cases.keys())} classes inited with file={filename}.", level="INFO")

    def run_legacy(
            self,
            message: MessageToSkill,
            context: Context,
            form: dict,
            text_preprocessing_result: TextPreprocessingResult,
            user: SMUser,
    ) -> str | None:
        """
        ## Запуск классификации.

        Args:
            message (nlpf_statemachine.models.message.protocol.assistant_message.BaseMessage): Тело запроса.
            context (nlpf_statemachine.models.context.Context): Контекст.
            form (dict[str, Any]): Форма.
            text_preprocessing_result (TextPreprocessingResult): NLPF TextPreprocessingResult.
            user (SMUser): NLPF User.

        Returns:
            str: результат классификации (event).
        """
        result = self.filler.extract(text_preprocessing_result, user)
        behaviour_log(f"Classification {self.id} result: {result}", level="DEBUG", user=user)
        return result


class ConstClassifier(Classifier):
    """
    # Классификатор возвращающий всегда постоянное значение.
    """

    def __init__(self, value: str, screen: str | None = None) -> None:
        super().__init__(id="IntersectionClassifier", screen=screen)
        self.value = value

    def run(self, message: MessageToSkill, context: Context, form: dict) -> str | None:
        """
        ## Запуск классификации.

        Args:
            message (nlpf_statemachine.models.message.protocol.assistant_message.BaseMessage): Тело запроса.
            context (nlpf_statemachine.models.context.Context): Контекст.
            form (dict[str, Any]): Форма.

        Returns:
            str: результат классификации (event).
        """
        return self.value

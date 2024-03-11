"""
# Создание NLPF Repository для StateMachine.

Модуль, в который нужно добавлять новые классы сценариев через включение в репозиторий.
"""
from typing import Any

from core.logging.logger_utils import behaviour_log
from core.repositories.base_repository import BaseRepository
from nlpf_statemachine.const import CONTEXT_MANAGER_ID


class SMRepository(BaseRepository):
    """
    # Класс-репозиторий для NLPF StateMachine сценариев.
    """

    def save(self, save_parameters: Any) -> None:
        """
        # Перепределение метода save.

        По факту не используется.

        Args:
            save_parameters (Any): параметры.

        Returns:
            None.
        """
        return

    def __init__(self, *args, **kwargs) -> None:
        context_manager = kwargs.pop("context_manager", None)
        super(SMRepository, self).__init__(*args, **kwargs)
        self._data = {}
        self._context_manager = context_manager

    def _add_context_manager(self, context_manager: Any) -> None:
        """
        ## Добавляем ContextManager в репозиторий.

        Args:
            context_manager (ContextManager): Менеджер контекста для NLPF StateMachine.

        Returns:
            None
        """
        if self._data.get(CONTEXT_MANAGER_ID):
            raise KeyError(
                f"StateMachineScenarioRepository:: dict scenario_descriptions already has scenario "
                f"with id={CONTEXT_MANAGER_ID}",
            )

        self._data[CONTEXT_MANAGER_ID] = context_manager
        behaviour_log(f"StateMachineScenarioRepository:: Добавлен сценарий {CONTEXT_MANAGER_ID}", level="INFO")

    def load(self) -> None:
        """
        ## Добавление новых сценариев.

        Returns:
            None
        """
        if self._context_manager:
            self._add_context_manager(context_manager=self._context_manager)
        else:
            behaviour_log("Context manager is not defined", level="ERROR")

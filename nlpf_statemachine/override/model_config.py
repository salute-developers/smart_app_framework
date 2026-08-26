"""
# Переопределение NLPF SmartAppResources.
"""

from nlpf_statemachine.const import STATE_MACHINE_REPOSITORY_NAME
from nlpf_statemachine.override.repository import SMRepository
from smart_kit.resources import SmartAppResources


class SMSmartAppResources(SmartAppResources):
    """
    # SmartAppResources для StateMachine.
    """

    CONTEXT_MANAGER = None

    def override_repositories(self, repositories: list) -> list:
        """
        # Переопределение репозиториев.

        В список репозиториев добавляется хранилище для машины состояний.

        Args:
            repositories (list): список репозиториев;

        Returns:
            list: обновлённый список.
        """
        return repositories + [SMRepository(key=STATE_MACHINE_REPOSITORY_NAME, context_manager=self.CONTEXT_MANAGER)]

"""
# Тесты на nlpf_statemachine.override.repository.
"""
from unittest import TestCase
from unittest.mock import MagicMock

from nlpf_statemachine.config import CONTEXT_MANAGER_ID
from nlpf_statemachine.override import SMRepository


class TestRepository(TestCase):
    """
    # Тесты на репозиторий StateMachine.
    """

    def setUp(self) -> None:
        """
        ## Базовая конфигурация теста.
        """
        self.context_manager = MagicMock()

    def test_load(self) -> None:
        """
        ## Тест на инициализацию репозиториев.
        """
        repository = SMRepository(
            key=CONTEXT_MANAGER_ID,
            context_manager=self.context_manager,
        )
        repository.load()
        assert repository.data == {CONTEXT_MANAGER_ID: self.context_manager}

    def test_second_load(self) -> None:
        """
        ## Тест на повторную инициализацию репозитория.
        """
        repository = SMRepository(
            key=CONTEXT_MANAGER_ID,
            context_manager=self.context_manager,
        )
        repository.load()
        try:
            repository.load()
            assert False
        except KeyError:
            assert True

    def test_load_without_context_manager(self) -> None:
        """
        ## Тест на инициализацию репозитория без context manager.
        """
        repository = SMRepository(
            key=CONTEXT_MANAGER_ID,
            context_manager=None,
        )
        repository.load()
        assert repository.data == {}

    def test_save(self) -> None:
        """
        ## Тест на инициализацию репозитория без context manager.
        """
        repository = SMRepository(
            key=CONTEXT_MANAGER_ID,
            context_manager=self.context_manager,
        )
        repository.load()
        assert repository.data == {CONTEXT_MANAGER_ID: self.context_manager}
        repository.save(save_parameters={"any": "param"})
        # Ничего не изменилось :)
        assert repository.data == {CONTEXT_MANAGER_ID: self.context_manager}

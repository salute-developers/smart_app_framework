"""
# Тесты на обработку таймаутов в интеграциях.
"""
from random import choice

from core.logging.logger_utils import behaviour_log
from nlpf_statemachine.config import TRANSACTION_MESSAGE_NAME_FINISH_LIST
from nlpf_statemachine.example.app.sc.models.context import ExampleContext
from nlpf_statemachine.example.app.user import ExampleUser
from nlpf_statemachine.kit import Screen
from nlpf_statemachine.models import AssistantState, Event
from tests.nlpf_statemachine_tests.utils import SMTestCase, action_mock, assert_action_call, random_string


class TestScenarioIntegrationTimeout(SMTestCase):
    """
    # Тесты на обработку таймаутов в интеграциях.

    Имеются 7 возможных кейсов:
        1. Есть локальный обработчик для таймаута в данной транзакции с указанием base_event.
        2. Есть локальный обработчик для таймаута в данной транзакции для любого base_event.
        3. Есть глобальный обработчик для таймаута в данной транзакции с указанием base_event.
        4. Есть глобальный обработчик для таймаута в данной транзакции для любого base_event.
        5. Нет глобальных/локальных обработчиков для таймаута в данной транзакции,
          но есть локальный дефолтный обработчик.
        6. Нет глобальных/локальных обработчиков для таймаута в данной транзакции,
          но есть глобальный дефолтный обработчик.
        7. Нет глобальных/локальных обработчиков, нет дефолтных обработчиков.
    """

    CONTEXT_CLASS = ExampleContext
    SMART_KIT_APP_CONFIG = "nlpf_statemachine.example.app_config"
    USER_CLASS = ExampleUser

    def setUp(self) -> None:
        """
        ## Базовая конфигурация теста.
        """
        super(TestScenarioIntegrationTimeout, self).setUp()
        self.base_event = random_string()
        self.request_name = random_string()
        self.screen = Screen(id=random_string())
        self.core.context_manager.add_screen(screen=self.screen)
        self.init(
            transaction_started=True,
            base_event=self.base_event,
            last_screen=self.screen.id,
            last_response_message_name=self.request_name,
        )
        self.message = self.mocks.local_timeout(
            message=self.mocks.message_to_skill(
                state=AssistantState(screen=self.screen.id),
            ),
        )

    async def test_integration_timeout_1_request_name_and_base_event_local(self) -> None:
        """
        ## Тест на кейс 1.

        Есть локальный обработчик для таймаута в данной транзакции с указанием base_event.
        """
        # ==== Mocks ====
        message_name = choice(TRANSACTION_MESSAGE_NAME_FINISH_LIST)
        action_request_name_and_base_event_local = action_mock(message_name=message_name)
        action_request_name_and_other_base_event_local = action_mock(message_name=message_name)
        action_request_name_local = action_mock(message_name=message_name)
        action_default_local = action_mock(message_name=message_name)
        action_request_name_and_base_event_global = action_mock(message_name=message_name)
        action_request_name_and_other_base_event_global = action_mock(message_name=message_name)
        action_request_name_global = action_mock(message_name=message_name)
        action_default_global = action_mock(message_name=message_name)

        self.screen.add_timeout_action(
            action=action_request_name_and_base_event_local,
            request_name=self.request_name,
            base_event=self.base_event,
            enabled=True,
        )
        self.screen.add_timeout_action(
            action=action_request_name_and_other_base_event_local,
            request_name=self.request_name,
            base_event=random_string(),
            enabled=True,
        )
        self.screen.add_timeout_action(
            action=action_request_name_local,
            request_name=self.request_name,
            enabled=True,
        )
        self.screen.add_timeout_action(
            action=action_default_local,
            enabled=True,
        )
        self.core.context_manager.add_timeout_action(
            action=action_request_name_and_base_event_global,
            request_name=self.request_name,
            base_event=self.base_event,
            enabled=True,
        )
        self.core.context_manager.add_timeout_action(
            action=action_request_name_and_other_base_event_global,
            request_name=self.request_name,
            base_event=random_string(),
            enabled=True,
        )
        self.core.context_manager.add_timeout_action(
            action=action_request_name_global,
            request_name=self.request_name,
            enabled=True,
        )
        self.core.context_manager.add_timeout_action(
            action=action_default_global,
            enabled=True,
        )

        # ==== Run ====
        await self.run_context_manager(
            event=Event.LOCAL_TIMEOUT,
            message=self.message,
        )

        # ==== Asserts ====
        assert_action_call(
            action=action_request_name_and_base_event_local,
            response=self.response,
            message=self.message,
            context=self.context,
            form={},
        )
        action_request_name_and_other_base_event_local.assert_not_called()
        action_request_name_local.assert_not_called()
        action_default_local.assert_not_called()
        action_request_name_and_base_event_global.assert_not_called()
        action_request_name_and_other_base_event_global.assert_not_called()
        action_request_name_global.assert_not_called()
        action_default_global.assert_not_called()
        self.assert_transaction_finished()

    async def test_integration_timeout_2_request_name_local(self) -> None:
        """
        ## Тест на кейс 2.

        Есть локальный обработчик для таймаута в данной транзакции для любого base_event.
        """
        # ==== Mocks ====

        message_name = choice(TRANSACTION_MESSAGE_NAME_FINISH_LIST)
        action_request_name_and_other_base_event_local = action_mock(message_name=message_name)
        action_request_name_local = action_mock(message_name=message_name)
        action_default_local = action_mock(message_name=message_name)
        action_request_name_and_base_event_global = action_mock(message_name=message_name)
        action_request_name_and_other_base_event_global = action_mock(message_name=message_name)
        action_request_name_global = action_mock(message_name=message_name)
        action_default_global = action_mock(message_name=message_name)

        self.screen.add_timeout_action(
            action=action_request_name_and_other_base_event_local,
            request_name=self.request_name,
            base_event=random_string(),
            enabled=True,
        )
        self.screen.add_timeout_action(
            action=action_request_name_local,
            request_name=self.request_name,
            enabled=True,
        )
        self.screen.add_timeout_action(
            action=action_default_local,
            enabled=True,
        )
        self.core.context_manager.add_timeout_action(
            action=action_request_name_and_base_event_global,
            request_name=self.request_name,
            base_event=self.base_event,
            enabled=True,
        )
        self.core.context_manager.add_timeout_action(
            action=action_request_name_and_other_base_event_global,
            request_name=self.request_name,
            base_event=random_string(),
            enabled=True,
        )
        self.core.context_manager.add_timeout_action(
            action=action_request_name_global,
            request_name=self.request_name,
            enabled=True,
        )
        self.core.context_manager.add_timeout_action(
            action=action_default_global,
            enabled=True,
        )

        # ==== Run ====
        await self.run_context_manager(
            event=Event.LOCAL_TIMEOUT,
            message=self.message,
        )

        # ==== Asserts ====
        assert_action_call(
            action=action_request_name_local,
            response=self.response,
            message=self.message,
            context=self.context,
            form={},
        )
        action_request_name_and_other_base_event_local.assert_not_called()
        action_default_local.assert_not_called()
        action_request_name_and_base_event_global.assert_not_called()
        action_request_name_and_other_base_event_global.assert_not_called()
        action_request_name_global.assert_not_called()
        action_default_global.assert_not_called()
        self.assert_transaction_finished()

    async def test_integration_timeout_3_request_name_and_base_event_global(self) -> None:
        """
        ## Тест на кейс 3.

        Есть глобальный обработчик для таймаута в данной транзакции с указанием base_event.
        """
        # ==== Mocks ====
        message_name = choice(TRANSACTION_MESSAGE_NAME_FINISH_LIST)
        action_request_name_and_other_base_event_local = action_mock(message_name=message_name)
        action_default_local = action_mock(message_name=message_name)
        action_request_name_and_base_event_global = action_mock(message_name=message_name)
        action_request_name_and_other_base_event_global = action_mock(message_name=message_name)
        action_request_name_global = action_mock(message_name=message_name)
        action_default_global = action_mock(message_name=message_name)

        self.screen.add_timeout_action(
            action=action_request_name_and_other_base_event_local,
            request_name=self.request_name,
            base_event=random_string(),
            enabled=True,
        )
        self.screen.add_timeout_action(
            action=action_default_local,
            enabled=True,
        )
        self.core.context_manager.add_timeout_action(
            action=action_request_name_and_base_event_global,
            request_name=self.request_name,
            base_event=self.base_event,
            enabled=True,
        )
        self.core.context_manager.add_timeout_action(
            action=action_request_name_and_other_base_event_global,
            request_name=self.request_name,
            base_event=random_string(),
            enabled=True,
        )
        self.core.context_manager.add_timeout_action(
            action=action_request_name_global,
            request_name=self.request_name,
            enabled=True,
        )
        self.core.context_manager.add_timeout_action(
            action=action_default_global,
            enabled=True,
        )

        # ==== Run ====
        await self.run_context_manager(
            event=Event.LOCAL_TIMEOUT,
            message=self.message,
        )

        # ==== Asserts ====
        assert_action_call(
            action=action_request_name_and_base_event_global,
            response=self.response,
            message=self.message,
            context=self.context,
            form={},
        )
        action_request_name_and_other_base_event_local.assert_not_called()
        action_default_local.assert_not_called()
        action_request_name_and_other_base_event_global.assert_not_called()
        action_request_name_global.assert_not_called()
        action_default_global.assert_not_called()
        self.assert_transaction_finished()

    async def test_integration_timeout_4_request_name_global(self) -> None:
        """
        ## Тест на кейс 4.

        Есть глобальный обработчик для таймаута в данной транзакции для любого base_event.
        """
        # ==== Mocks ====
        message_name = choice(TRANSACTION_MESSAGE_NAME_FINISH_LIST)
        action_request_name_and_other_base_event_local = action_mock(message_name=message_name)
        action_default_local = action_mock(message_name=message_name)
        action_request_name_and_other_base_event_global = action_mock(message_name=message_name)
        action_request_name_global = action_mock(message_name=message_name)
        action_default_global = action_mock(message_name=message_name)

        self.screen.add_timeout_action(
            action=action_request_name_and_other_base_event_local,
            request_name=self.request_name,
            base_event=random_string(),
            enabled=True,
        )
        self.screen.add_timeout_action(
            action=action_default_local,
            enabled=True,
        )
        self.core.context_manager.add_timeout_action(
            action=action_request_name_and_other_base_event_global,
            request_name=self.request_name,
            base_event=random_string(),
            enabled=True,
        )
        self.core.context_manager.add_timeout_action(
            action=action_request_name_global,
            request_name=self.request_name,
            enabled=True,
        )
        self.core.context_manager.add_timeout_action(
            action=action_default_global,
            enabled=True,
        )

        # ==== Run ====
        await self.run_context_manager(
            event=Event.LOCAL_TIMEOUT,
            message=self.message,
        )

        # ==== Asserts ====
        assert_action_call(
            action=action_request_name_global,
            response=self.response,
            message=self.message,
            context=self.context,
            form={},
        )
        action_request_name_and_other_base_event_local.assert_not_called()
        action_default_local.assert_not_called()
        action_request_name_and_other_base_event_global.assert_not_called()
        action_default_global.assert_not_called()
        self.assert_transaction_finished()

    async def test_integration_timeout_5_default_local(self) -> None:
        """
        ## Тест на кейс 5.

        Нет глобальных/локальных обработчиков для таймаута в данной транзакции, но есть локальный дефолтный обработчик.
        """
        # ==== Mocks ====
        message_name = choice(TRANSACTION_MESSAGE_NAME_FINISH_LIST)
        action_request_name_and_other_base_event_local = action_mock(message_name=message_name)
        action_default_local = action_mock(message_name=message_name)
        action_request_name_and_other_base_event_global = action_mock(message_name=message_name)
        action_default_global = action_mock(message_name=message_name)

        self.screen.add_timeout_action(
            action=action_request_name_and_other_base_event_local,
            request_name=self.request_name,
            base_event=random_string(),
            enabled=True,
        )
        self.screen.add_timeout_action(
            action=action_default_local,
            enabled=True,
        )
        self.core.context_manager.add_timeout_action(
            action=action_request_name_and_other_base_event_global,
            request_name=self.request_name,
            base_event=random_string(),
            enabled=True,
        )
        self.core.context_manager.add_timeout_action(
            action=action_default_global,
            enabled=True,
        )

        # ==== Run ====
        await self.run_context_manager(
            event=Event.LOCAL_TIMEOUT,
            message=self.message,
        )

        # ==== Asserts ====
        assert_action_call(
            action=action_default_local,
            response=self.response,
            message=self.message,
            context=self.context,
            form={},
        )
        action_request_name_and_other_base_event_local.assert_not_called()
        action_request_name_and_other_base_event_global.assert_not_called()
        action_default_global.assert_not_called()
        self.assert_transaction_finished()

    async def test_integration_timeout_6_default_global(self) -> None:
        """
        ## Тест на кейс 6.

        Нет глобальных/локальных обработчиков для таймаута в данной транзакции, но есть глобальный дефолтный обработчик.
        """
        # ==== Mocks ====
        message_name = choice(TRANSACTION_MESSAGE_NAME_FINISH_LIST)
        action_request_name_and_other_base_event_local = action_mock(message_name=message_name)
        action_request_name_and_other_base_event_global = action_mock(message_name=message_name)
        action_default_global = action_mock(message_name=message_name)

        self.screen.add_timeout_action(
            action=action_request_name_and_other_base_event_local,
            request_name=self.request_name,
            base_event=random_string(),
            enabled=True,
        )
        self.core.context_manager.add_timeout_action(
            action=action_request_name_and_other_base_event_global,
            request_name=self.request_name,
            base_event=random_string(),
            enabled=True,
        )
        self.core.context_manager.add_timeout_action(
            action=action_default_global,
            enabled=True,
        )

        # ==== Run ====
        await self.run_context_manager(
            event=Event.LOCAL_TIMEOUT,
            message=self.message,
        )

        # ==== Asserts ====
        assert_action_call(
            action=action_default_global,
            response=self.response,
            message=self.message,
            context=self.context,
            form={},
        )
        action_request_name_and_other_base_event_local.assert_not_called()
        action_request_name_and_other_base_event_global.assert_not_called()
        self.assert_transaction_finished()

    async def test_integration_timeout_7_no_timeout_handler(self) -> None:
        """
        ## Тест на кейс 7.

        Нет глобальных/локальных обработчиков, нет дефолтных обработчиков.
        """
        # ==== Mocks ====
        message_name = choice(TRANSACTION_MESSAGE_NAME_FINISH_LIST)
        action_request_name_and_other_base_event_local = action_mock(message_name=message_name)
        action_request_name_and_other_base_event_global = action_mock(message_name=message_name)

        self.screen.add_timeout_action(
            action=action_request_name_and_other_base_event_local,
            request_name=self.request_name,
            base_event=random_string(),
            enabled=True,
        )
        self.core.context_manager.add_timeout_action(
            action=action_request_name_and_other_base_event_global,
            request_name=self.request_name,
            base_event=random_string(),
            enabled=True,
        )
        behaviour_log(self.core.context_manager.global_scenario.timeout_actions)
        # ==== Run ====
        await self.run_context_manager(
            event=Event.LOCAL_TIMEOUT,
            message=self.message,
        )

        # ==== Asserts ====
        action_request_name_and_other_base_event_local.assert_not_called()
        action_request_name_and_other_base_event_global.assert_not_called()
        self.assert_no_response()
        self.assert_transaction_finished()

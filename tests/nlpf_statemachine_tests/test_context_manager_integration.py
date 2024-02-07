"""
# Тесты на работу интеграций.
"""
from random import choice

from nlpf_statemachine.example.app.sc.models.context import ExampleContext
from nlpf_statemachine.example.app.sc.models.message import CustomMessageToSkill, CustomState
from nlpf_statemachine.example.app.user import ExampleUser
from nlpf_statemachine.config import SMConfig
from nlpf_statemachine.kit import Screen
from nlpf_statemachine.models import IntegrationMessage
from tests.nlpf_statemachine_tests.utils import (
    AnyObj,
    SMAsyncioTestCase,
    action_integration_mock,
    action_mock,
    assert_action_call,
    classifier_mock,
    random_string,
)


class TestScenarioIntegration(SMAsyncioTestCase):
    """
    # Тесты на работу интеграций.

    Имеются 5 возможных кейсов:
        1. Найдётся локальный обработчик события от интеграции с указанием base_event;
        2. Найдётся локальный обработчик события от интеграции без указания base_event;
        3. Найдётся глобальный обработчик события от интеграции с указанием base_event;
        4. Найдётся глобальный обработчик события от интеграции без указания base_event;
        5. Не найдётся обработчика на событие.
    """

    CONTEXT_CLASS = ExampleContext
    SMART_KIT_APP_CONFIG = "nlpf_statemachine.example.app_config"
    USER_CLASS = ExampleUser

    def setUp(self) -> None:
        """
        ## Базовая конфигурация теста.
        """
        super(TestScenarioIntegration, self).setUp()
        self.init()
        self.screen = Screen(id=random_string())
        self.core.context_manager.add_screen(screen=self.screen)
        self.message = self.mocks.message_to_skill(
            cls=CustomMessageToSkill,
            state=CustomState(screen=self.screen.id),
        )
        self.integration_response = IntegrationMessage(messageName=random_string(), payload={})

    async def test_integration_1_with_response_on_event_and_base_event_local(self) -> None:
        """
        ## Тест 1: Найдётся локальный обработчик события от интеграции с указанием base_event.
        """
        # ==== Mocks ====
        action = action_integration_mock()
        classifier = classifier_mock(run_mock=action.event)
        self.core.context_manager.add_action(event=action.event, action=action)
        self.core.context_manager.add_classifier(classifier=classifier)

        message_name = choice(SMConfig.transaction_massage_name_finish_list)
        action_on_event_local = action_mock(message_name=message_name)
        action_on_event_and_base_event_local = action_mock(message_name=message_name)
        action_on_event_and_other_base_event_local = action_mock(message_name=message_name)
        action_on_event_global = action_mock(message_name=message_name)
        action_on_event_and_base_event_global = action_mock(message_name=message_name)
        action_on_event_and_other_base_event_global = action_mock(message_name=message_name)

        self.screen.add_action(
            event=self.integration_response.messageName,
            action=action_on_event_local,
            enabled=True,
        )
        self.screen.add_action(
            event=self.integration_response.messageName,
            base_event=action.event,
            action=action_on_event_and_base_event_local,
            enabled=True,
        )
        self.screen.add_action(
            event=self.integration_response.messageName,
            base_event=random_string(),
            action=action_on_event_and_other_base_event_local,
            enabled=True,
        )
        self.core.context_manager.add_action(
            event=self.integration_response.messageName,
            action=action_on_event_global,
            enabled=True,
        )
        self.core.context_manager.add_action(
            event=self.integration_response.messageName,
            base_event=action.event,
            action=action_on_event_and_base_event_global,
            enabled=True,
        )
        self.core.context_manager.add_action(
            event=self.integration_response.messageName,
            base_event=random_string(),
            action=action_on_event_and_other_base_event_global,
            enabled=True,
        )

        # ==== Run 1 (start integration) ====
        await self.run_context_manager(message=self.message)

        # ==== Asserts ====
        assert_action_call(
            action=action,
            response=self.response,
            message=self.message,
            context=self.context,
            form=AnyObj(),
        )
        self.assert_transaction_started()
        action_on_event_local.assert_not_called()
        action_on_event_and_base_event_local.assert_not_called()
        action_on_event_global.assert_not_called()
        action_on_event_and_base_event_global.assert_not_called()
        action_on_event_and_other_base_event_local.assert_not_called()
        action_on_event_and_other_base_event_global.assert_not_called()

        # ==== Run 2 (continue integration) ====
        await self.run_context_manager(message=self.integration_response, event=self.integration_response.messageName)

        # ==== Asserts ====
        assert_action_call(
            action=action_on_event_and_base_event_local,
            response=self.response,
            message=self.integration_response,
            context=self.context,
            form=AnyObj(),
        )
        action.assert_called_once()
        action_on_event_local.assert_not_called()
        action_on_event_global.assert_not_called()
        action_on_event_and_base_event_global.assert_not_called()
        action_on_event_and_other_base_event_local.assert_not_called()
        action_on_event_and_other_base_event_global.assert_not_called()
        self.assert_transaction_finished()

    async def test_integration_2_with_response_on_event_local(self) -> None:
        """
        ## Тест 2: Найдётся локальный обработчик события от интеграции без указания base_event.
        """
        # ==== Mocks ====
        action = action_integration_mock()
        classifier = classifier_mock(run_mock=action.event)
        self.core.context_manager.add_action(event=action.event, action=action)
        self.core.context_manager.add_classifier(classifier=classifier)

        message_name = choice(SMConfig.transaction_massage_name_finish_list)
        action_on_event_local = action_mock(message_name=message_name)
        action_on_event_and_other_base_event_local = action_mock(message_name=message_name)
        action_on_event_global = action_mock(message_name=message_name)
        action_on_event_and_base_event_global = action_mock(message_name=message_name)
        action_on_event_and_other_base_event_global = action_mock(message_name=message_name)

        self.screen.add_action(
            event=self.integration_response.messageName,
            action=action_on_event_local,
            enabled=True,
        )
        self.screen.add_action(
            event=self.integration_response.messageName,
            base_event=random_string(),
            action=action_on_event_and_other_base_event_local,
            enabled=True,
        )
        self.core.context_manager.add_action(
            event=self.integration_response.messageName,
            action=action_on_event_global,
            enabled=True,
        )
        self.core.context_manager.add_action(
            event=self.integration_response.messageName,
            base_event=action.event,
            action=action_on_event_and_base_event_global,
            enabled=True,
        )
        self.core.context_manager.add_action(
            event=self.integration_response.messageName,
            base_event=random_string(),
            action=action_on_event_and_other_base_event_global,
            enabled=True,
        )

        # ==== Run 1 (start integration) ====
        await self.run_context_manager(message=self.message)

        # ==== Asserts ====
        assert_action_call(
            action=action,
            response=self.response,
            message=self.message,
            context=self.context,
            form=AnyObj(),
        )
        self.assert_transaction_started()
        action_on_event_local.assert_not_called()
        action_on_event_global.assert_not_called()
        action_on_event_and_base_event_global.assert_not_called()
        action_on_event_and_other_base_event_local.assert_not_called()
        action_on_event_and_other_base_event_global.assert_not_called()

        # ==== Run 2 (continue integration) ====
        await self.run_context_manager(message=self.integration_response, event=self.integration_response.messageName)

        # ==== Asserts ====
        assert_action_call(
            action=action_on_event_local,
            response=self.response,
            message=self.integration_response,
            context=self.context,
            form=AnyObj(),
        )
        action.assert_called_once()
        action_on_event_global.assert_not_called()
        action_on_event_and_base_event_global.assert_not_called()
        action_on_event_and_other_base_event_local.assert_not_called()
        action_on_event_and_other_base_event_global.assert_not_called()
        self.assert_transaction_finished()

    async def test_integration_3_with_response_on_event_and_base_event_global(self) -> None:
        """
        ## Тест 3: Найдётся глобальный обработчик события от интеграции с указанием base_event.
        """
        # ==== Mocks ====
        action = action_integration_mock()
        classifier = classifier_mock(run_mock=action.event)
        self.core.context_manager.add_action(event=action.event, action=action)
        self.core.context_manager.add_classifier(classifier=classifier)

        message_name = choice(SMConfig.transaction_massage_name_finish_list)
        action_on_event_and_other_base_event_local = action_mock(message_name=message_name)
        action_on_event_global = action_mock(message_name=message_name)
        action_on_event_and_base_event_global = action_mock(message_name=message_name)
        action_on_event_and_other_base_event_global = action_mock(message_name=message_name)

        self.screen.add_action(
            event=self.integration_response.messageName,
            base_event=random_string(),
            action=action_on_event_and_other_base_event_local,
            enabled=True,
        )
        self.core.context_manager.add_action(
            event=self.integration_response.messageName,
            action=action_on_event_global,
            enabled=True,
        )
        self.core.context_manager.add_action(
            event=self.integration_response.messageName,
            base_event=action.event,
            action=action_on_event_and_base_event_global,
            enabled=True,
        )
        self.core.context_manager.add_action(
            event=self.integration_response.messageName,
            base_event=random_string(),
            action=action_on_event_and_other_base_event_global,
            enabled=True,
        )

        # ==== Run 1 (start integration) ====
        await self.run_context_manager(message=self.message)

        # ==== Asserts ====
        assert_action_call(
            action=action,
            response=self.response,
            message=self.message,
            context=self.context,
            form=AnyObj(),
        )
        self.assert_transaction_started()
        action_on_event_global.assert_not_called()
        action_on_event_and_base_event_global.assert_not_called()
        action_on_event_and_other_base_event_local.assert_not_called()
        action_on_event_and_other_base_event_global.assert_not_called()

        # ==== Run 2 (continue integration) ====
        await self.run_context_manager(message=self.integration_response, event=self.integration_response.messageName)

        # ==== Asserts ====
        assert_action_call(
            action=action_on_event_and_base_event_global,
            response=self.response,
            message=self.integration_response,
            context=self.context,
            form=AnyObj(),
        )
        action.assert_called_once()
        action_on_event_global.assert_not_called()
        action_on_event_and_other_base_event_local.assert_not_called()
        action_on_event_and_other_base_event_global.assert_not_called()
        self.assert_transaction_finished()

    async def test_integration_4_with_response_on_event_global(self) -> None:
        """
        ## Тест 4: Найдётся глобальный обработчик события от интеграции без указания base_event.
        """
        # ==== Mocks ====
        action = action_integration_mock()
        classifier = classifier_mock(run_mock=action.event)
        self.core.context_manager.add_action(event=action.event, action=action)
        self.core.context_manager.add_classifier(classifier=classifier)

        message_name = choice(SMConfig.transaction_massage_name_finish_list)
        action_on_event_and_other_base_event_local = action_mock(message_name=message_name)
        action_on_event_global = action_mock(message_name=message_name)
        action_on_event_and_other_base_event_global = action_mock(message_name=message_name)

        self.screen.add_action(
            event=self.integration_response.messageName,
            base_event=random_string(),
            action=action_on_event_and_other_base_event_local,
            enabled=True,
        )
        self.core.context_manager.add_action(
            event=self.integration_response.messageName,
            action=action_on_event_global,
            enabled=True,
        )
        self.core.context_manager.add_action(
            event=self.integration_response.messageName,
            base_event=random_string(),
            action=action_on_event_and_other_base_event_global,
            enabled=True,
        )

        # ==== Run 1 (start integration) ====
        await self.run_context_manager(message=self.message)

        # ==== Asserts ====
        assert_action_call(
            action=action,
            response=self.response,
            message=self.message,
            context=self.context,
            form=AnyObj(),
        )
        self.assert_transaction_started()
        action_on_event_global.assert_not_called()
        action_on_event_and_other_base_event_local.assert_not_called()
        action_on_event_and_other_base_event_global.assert_not_called()

        # ==== Run 2 (continue integration) ====
        await self.run_context_manager(message=self.integration_response, event=self.integration_response.messageName)

        # ==== Asserts ====
        assert_action_call(
            action=action_on_event_global,
            response=self.response,
            message=self.integration_response,
            context=self.context,
            form=AnyObj(),
        )
        action.assert_called_once()
        action_on_event_and_other_base_event_local.assert_not_called()
        action_on_event_and_other_base_event_global.assert_not_called()
        self.assert_transaction_finished()

    async def test_integration_5_no_action_on_response(self) -> None:
        """
        ## Тест 5: Не найдётся обработчика на событие.
        """
        # ==== Mocks ====
        action = action_integration_mock()
        classifier = classifier_mock(run_mock=action.event)
        self.core.context_manager.add_action(event=action.event, action=action)
        self.core.context_manager.add_classifier(classifier=classifier)

        message_name = choice(SMConfig.transaction_massage_name_finish_list)
        action_on_event_and_other_base_event_local = action_mock(message_name=message_name)
        action_on_event_and_other_base_event_global = action_mock(message_name=message_name)

        self.screen.add_action(
            event=self.integration_response.messageName,
            base_event=random_string(),
            action=action_on_event_and_other_base_event_local,
            enabled=True,
        )
        self.core.context_manager.add_action(
            event=self.integration_response.messageName,
            base_event=random_string(),
            action=action_on_event_and_other_base_event_global,
            enabled=True,
        )

        # ==== Run 1 (start integration) ====
        await self.run_context_manager(message=self.message)

        # ==== Asserts ====
        assert_action_call(
            action=action,
            response=self.response,
            message=self.message,
            context=self.context,
            form=AnyObj(),
        )
        self.assert_transaction_started()
        action_on_event_and_other_base_event_local.assert_not_called()
        action_on_event_and_other_base_event_global.assert_not_called()

        # ==== Run 2 (continue integration) ====
        await self.run_context_manager(message=self.integration_response, event=self.integration_response.messageName)

        # ==== Asserts ====
        action.assert_called_once()
        action_on_event_and_other_base_event_local.assert_not_called()
        action_on_event_and_other_base_event_global.assert_not_called()
        self.assert_transaction_finished()
        self.assert_no_response()

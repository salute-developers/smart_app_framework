"""
# Тесты на обработку ошибок в эшкенах.
"""
from nlpf_statemachine.example.app.sc.models.context import ExampleContext
from nlpf_statemachine.example.app.user import ExampleUser
from nlpf_statemachine.kit import ContextManager, Screen
from nlpf_statemachine.models import AssistantState, BaseMessage, Context
from tests.nlpf_statemachine_tests.utils import (
    SMTestCase,
    action_mock,
    action_with_exception_mock,
    assert_action_call,
    random_string,
)


class TestContextManagerExceptions(SMTestCase):
    """
    # Тесты на обработку ошибок в эшкенах.
    """

    CONTEXT_CLASS = ExampleContext
    SMART_KIT_APP_CONFIG = "nlpf_statemachine.example.app_config"
    USER_CLASS = ExampleUser

    def setUp(self) -> None:
        """
        ## Конфигурация базовых параметров перед запуском тестов.
        """
        super(TestContextManagerExceptions, self).setUp()
        self.context_manager = ContextManager()
        self.action = action_with_exception_mock()
        self.event = random_string()
        self.context_manager.add_action(event=self.event, action=self.action)
        self.message = BaseMessage(messageName="TEST")
        self.user = self.mocks.user(message=self.message)
        self.context = Context()
        self.text_preprocessing_result = self.mocks.text_preprocessing_result()

    async def test_action_exception_without_error_actions(self) -> None:
        """
        ## Тест на обработку ошибки в экшене без определённых экшенов обработки ошибок.

        ОР: вернётся ERROR.
        """
        # ==== Run ====
        self.response = await self.context_manager.run(
            event=self.event,
            message=self.message,
            context=self.context,
            text_preprocessing_result=self.text_preprocessing_result,
            user=self.user,
        )
        # ==== Asserts ====
        self.action.assert_called_with(message=self.message, context=self.context, form={})
        self.assert_error()

    async def test_action_exception_with_global_error_action(self) -> None:
        """
        ## Тест на обработку ошибки с глобальным error_action.

        ОР: вернётся ответ из error_action.
        """
        # ==== Mocks ====
        error_action = action_mock()
        self.context_manager.add_error_action(action=error_action)

        # ==== Run ====
        self.response = await self.context_manager.run(
            event=self.event,
            message=self.message,
            context=self.context,
            text_preprocessing_result=self.text_preprocessing_result,
            user=self.user,
        )

        # ==== Asserts ====
        self.action.assert_called_with(message=self.message, context=self.context, form={})
        assert_action_call(
            action=error_action,
            response=self.response,
            message=self.message,
            context=self.context,
            form={},
        )
        assert self.response == error_action.return_value

    async def test_action_exception_with_broken_global_error_action(self) -> None:
        """
        ## Тест на обработку ошибки с глобальным error_action, который бросает exception.

        ОР: вернётся ERROR.
        """
        # ==== Mocks ====
        error_action = action_with_exception_mock()
        self.context_manager.add_error_action(action=error_action)

        # ==== Run ====
        self.response = await self.context_manager.run(
            event=self.event,
            message=self.message,
            context=self.context,
            text_preprocessing_result=self.text_preprocessing_result,
            user=self.user,
        )

        # ==== Asserts ====
        self.action.assert_called_with(message=self.message, context=self.context, form={})
        error_action.assert_called_with(message=self.message, context=self.context, form={})
        self.assert_error()

    async def test_action_exception_with_error_action_on_screen(self) -> None:
        """
        ## Тест на обработку ошибки на странице с error_action.

        ОР: вернётся ответ от error_action на странице.
        """
        # ==== Mocks ====
        screen_name = random_string()
        screen = Screen(screen_name)
        error_action_global = action_mock(payload={"key": "GLOBAL ERROR ACTION"})
        error_action_screen = action_mock(payload={"key": "SCREEN ERROR ACTION"})
        screen.add_error_action(action=error_action_screen)
        self.context_manager.add_screen(screen)
        self.context_manager.add_error_action(action=error_action_global)
        self.message = self.mocks.message_to_skill(state=AssistantState(screen=screen_name))

        # ==== Run ====
        self.response = await self.context_manager.run(
            event=self.event,
            message=self.message,
            context=self.context,
            text_preprocessing_result=self.text_preprocessing_result,
            user=self.user,
        )

        # ==== Asserts ====
        self.action.assert_called_with(message=self.message, context=self.context, form={})
        error_action_global.assert_not_called()
        assert_action_call(
            action=error_action_screen,
            response=self.response,
            message=self.message,
            context=self.context,
            form={},
        )
        assert self.response.payload == {"key": "SCREEN ERROR ACTION"}

    async def test_action_exception_with_broken_error_action_on_screen(self) -> None:
        """
        ## Тест на обработку ошибки на странице с error_action, который бросает exception.

        ОР: вернётся ERROR.
        """
        # ==== Mocks ====
        screen_name = random_string()
        screen = Screen(screen_name)
        error_action_global = action_mock(payload={"key": "GLOBAL ERROR ACTION"})
        error_action_screen = action_with_exception_mock()
        screen.add_error_action(action=error_action_screen)
        self.context_manager.add_screen(screen)
        self.context_manager.add_error_action(action=error_action_global)
        self.message = self.mocks.message_to_skill(state=AssistantState(screen=screen_name))

        # ==== Run ====
        self.response = await self.context_manager.run(
            event=self.event,
            message=self.message,
            context=self.context,
            text_preprocessing_result=self.text_preprocessing_result,
            user=self.user,
        )

        # ==== Asserts ====
        self.action.assert_called_with(message=self.message, context=self.context, form={})
        error_action_screen.assert_called_with(message=self.message, context=self.context, form={})
        error_action_global.assert_not_called()
        self.assert_error()

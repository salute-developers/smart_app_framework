"""
# Тесты на простой запуск ContextManager.
"""

from nlpf_statemachine.example.app.sc.models.context import ExampleContext
from nlpf_statemachine.example.app.user import ExampleUser
from nlpf_statemachine.kit import ContextManager
from nlpf_statemachine.models import BaseMessage, Context, DoNothing, ErrorResponse, NothingFound
from tests.nlpf_statemachine_tests.utils import SMAsyncioTestCase, action_mock, random_string


class TestScenarioSimpleEvent(SMAsyncioTestCase):
    """
    # Тесты на простой запуск сценария с каким-либо событием.
    """

    CONTEXT_CLASS = ExampleContext
    SMART_KIT_APP_CONFIG = "nlpf_statemachine.example.app_config"
    USER_CLASS = ExampleUser

    async def test_nothing_found_context_manager(self) -> None:
        """
        ## Тест на холостой запуск с флагом run_smart_app_framework_base_kit=False.

        ОР: Если флаг run_smart_app_framework_base_kit == False, то вернётся NothingFound, иначе вернётся None.
        """
        message = BaseMessage(messageName="TEST")
        context = Context()
        text_preprocessing_result = self.mocks.text_preprocessing_result(payload={})
        user = self.mocks.user(message=message)

        context_manager = ContextManager()
        response = await context_manager.run(
            event=None,
            message=message,
            context=context,
            text_preprocessing_result=text_preprocessing_result,
            user=user,
        )
        assert response == NothingFound()

        context_manager = ContextManager(run_smart_app_framework_base_kit=True)
        response = await context_manager.run(
            event=None,
            message=message,
            context=context,
            text_preprocessing_result=text_preprocessing_result,
            user=user,
        )
        assert response is None

    async def test_do_nothing_context_manager(self) -> None:
        """
        ## Тест на запуск события, на который нет обработчика.

        ОР: Если флаг run_smart_app_framework_base_kit == False, то вернётся DoNothing, иначе вернётся None.
        """
        event = random_string()
        message = BaseMessage(messageName="TEST")
        context = Context()
        text_preprocessing_result = self.mocks.text_preprocessing_result(payload={})
        user = self.mocks.user(message=message)

        context_manager = ContextManager()
        response = await context_manager.run(
            event=event,
            message=message,
            context=context,
            text_preprocessing_result=text_preprocessing_result,
            user=user,
        )
        assert response == DoNothing()

        context_manager = ContextManager(run_smart_app_framework_base_kit=True)
        response = await context_manager.run(
            event=event,
            message=message,
            context=context,
            text_preprocessing_result=text_preprocessing_result,
            user=user,
        )
        assert response is None

    async def test_simple_event_no_response_without_fallback(self) -> None:
        """
        ## Тест на запуск события с простым обработчиком, возвращающим что-то непонятное (без fallback).

        ОР: ничего не произойдёт, вернётся дефолтный ответ для события.
        """
        event = random_string()
        message = BaseMessage(messageName="TEST")
        context = Context()
        text_preprocessing_result = self.mocks.text_preprocessing_result(payload={})
        user = self.mocks.user(message=message)
        context_manager = ContextManager()
        action = action_mock()
        action.return_value = {"some": "value"}
        context_manager.add_action(event=event, action=action)

        response = await context_manager.run(
            event=event,
            message=message,
            context=context,
            text_preprocessing_result=text_preprocessing_result,
            user=user,
        )

        # ==== Asserts ====
        action.assert_called_with(message=message, context=context, form={})
        assert response == ErrorResponse()

    async def test_simple_event_no_response_with_fallback(self) -> None:
        """
        ## Тест на запуск события с простым обработчиком, возвращающим что-то непонятное (при этом fallback есть).

        ОР: ничего не произойдёт, вернётся дефолтный ответ для события.
        """
        event = random_string()
        message = BaseMessage(messageName="TEST")
        context = Context()
        text_preprocessing_result = self.mocks.text_preprocessing_result(payload={})
        user = self.mocks.user(message=message)
        context_manager = ContextManager()
        action = action_mock()
        action.return_value = {"value": random_string()}
        fallback = action_mock(payload={"value": random_string()})
        context_manager.add_action(event=event, action=action)
        context_manager.add_fallback_action(action=fallback)

        response = await context_manager.run(
            event=event,
            message=message,
            context=context,
            text_preprocessing_result=text_preprocessing_result,
            user=user,
        )

        # ==== Asserts ====
        action.assert_called_with(message=message, context=context, form={})
        fallback.assert_not_called()
        assert response == ErrorResponse()

    async def test_simple_event_with_response(self) -> None:
        """
        # Тест на запуск события с простым обработчиком, возвращающим хороший ответ.

        ОР: Возвращается ответ из обарботчика.
        """
        event = random_string()
        message = BaseMessage(messageName="TEST")
        context = Context()
        text_preprocessing_result = self.mocks.text_preprocessing_result(payload={})
        user = self.mocks.user(message=message)
        context_manager = ContextManager()
        action = action_mock(payload={"value": random_string()})
        fallback = action_mock(payload={"value": random_string()})
        context_manager.add_action(event=event, action=action)
        context_manager.add_fallback_action(action=fallback)

        response = await context_manager.run(
            event=event,
            message=message,
            context=context,
            text_preprocessing_result=text_preprocessing_result,
            user=user,
        )

        # ==== Asserts ====
        action.assert_called_with(message=message, context=context, form={})
        fallback.assert_not_called()
        assert response == action.return_value

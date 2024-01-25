"""
# Тесты на работу классификации при наличии страниц.
"""
from unittest.mock import MagicMock

from nlpf_statemachine.example.app.sc.models.context import ExampleContext
from nlpf_statemachine.example.app.user import ExampleUser
from nlpf_statemachine.kit import ContextManager, Screen
from nlpf_statemachine.models import AssistantState, Context
from tests.nlpf_statemachine_tests.utils import (
    SMTestCase,
    action_mock,
    assert_action_call,
    classifier_mock,
    random_string,
)


class TestScenarioWithScreen(SMTestCase):
    """
    # Тесты на работу классификации при наличии страниц.
    """

    CONTEXT_CLASS = ExampleContext
    SMART_KIT_APP_CONFIG = "nlpf_statemachine.example.app_config"
    USER_CLASS = ExampleUser

    def setUp(self) -> None:
        """
        ## Конфигурация базовых параметров перед запуском тестов.
        """
        super(TestScenarioWithScreen, self).setUp()
        self.context_manager = ContextManager()
        self.context = Context()

        self.global_action = action_mock(payload={"key": "global_action"})
        self.global_fallback_action = action_mock(payload={"key": "global_fallback"})

        # ==== Screen 1 ====
        self.screen_1_name = random_string()
        self.screen_1 = Screen(self.screen_1_name)
        self.bad_action_event = random_string()
        self.bad_action = action_mock()
        self.bad_action.return_value = None
        self.action_1 = action_mock(payload={"key": "action_1"})
        self.screen_fallback_action = action_mock(payload={"key": "screen_fallback"})

        self.screen_1.add_action(event=self.action_1.event, action=self.action_1)
        self.screen_1.add_action(event=self.bad_action_event, action=self.bad_action)
        self.screen_1.add_fallback_action(action=self.screen_fallback_action)

        # ==== Screen 2: no fallback ====
        self.screen_2_name = random_string()
        self.screen_2 = Screen(self.screen_2_name)
        self.screen_2.add_action(event=self.action_1.event, action=self.action_1)
        self.screen_2.add_action(event=self.bad_action_event, action=self.bad_action)

        # ==== Scenario ====
        self.broken_global_action = action_mock()
        self.broken_global_action.return_value = None
        self.broken_global_action_event = random_string()
        self.global_classifier = classifier_mock(run_mock=self.global_action.event)
        self.context_manager.add_action(event=self.global_action.event, action=self.global_action)
        self.context_manager.add_action(event=self.broken_global_action_event, action=self.broken_global_action)
        self.context_manager.add_fallback_action(action=self.global_fallback_action)
        self.context_manager.add_classifier(classifier=self.global_classifier)

    async def test_screen_classification_local_event(self) -> None:
        """
        ## Тест на классификакцию локального интента на странице.

        ОР: Вызовется классификатор на страниц. Найдёт интент.
        Классификатор глобальный вызван не будет. Отработает локальный обработчик.
        """
        # ==== Mocks ====
        message = self.mocks.message_to_skill(state=AssistantState(screen=self.screen_1_name))
        classifier = classifier_mock(run_mock=self.action_1.event)
        self.screen_1.add_classifier(classifier=classifier)
        self.context_manager.add_screen(screen=self.screen_1)

        # ==== Run ====
        self.response = await self.context_manager.run(
            event=None,
            message=message,
            context=self.context,
            text_preprocessing_result=self.text_preprocessing_result,
            user=self.mocks.user(message=message),
        )

        # ==== Asserts ====
        classifier.run.assert_called_with(message=message, context=self.context, form={})
        assert_action_call(
            action=self.action_1,
            response=self.response,
            message=message,
            context=self.context,
            form={},
        )

    async def test_screen_classification_local_event_no_response(self) -> None:
        """
        ## Тест на классификакцию локального интента на странице, у которого экшен не отвечает.

        ОР: Вызовется классификатор на странице. Найдёт интент.
        Классификатор глобальный вызван не будет. Отработает локальный обработчик. Вернёт None.
        Вернётся ошибка, ибо обработчик всегда должен возвращать объект наследник Response.
        """
        # ==== Mocks ====
        message = self.mocks.message_to_skill(state=AssistantState(screen=self.screen_1_name))
        classifier = classifier_mock(run_mock=self.bad_action_event)
        self.screen_1.add_classifier(classifier=classifier)
        self.context_manager.add_screen(screen=self.screen_1)

        # ==== Run ====
        self.response = await self.context_manager.run(
            event=None,
            message=message,
            context=self.context,
            text_preprocessing_result=self.text_preprocessing_result,
            user=self.mocks.user(message=message),
        )

        # ==== Asserts ====
        classifier.run.assert_called_with(message=message, context=self.context, form={})
        self.bad_action.assert_called_with(message=message, context=self.context, form={})
        self.assert_error()

    async def test_screen_classification_global_event(self) -> None:
        """
        ## Тест на вызов глоабльного интента.

        ОР: Вызовется классификатор на странице. Интент не найден.
        Вызовется глобальный классификатор. Отработает глобальный обработчик.
        """
        # ==== Mocks ====
        message = self.mocks.message_to_skill(state=AssistantState(screen=self.screen_1_name))
        self.context_manager.add_screen(screen=self.screen_1)

        # ==== Run ====
        self.response = await self.context_manager.run(
            event=None,
            message=message,
            context=self.context,
            text_preprocessing_result=self.text_preprocessing_result,
            user=self.mocks.user(message=message),
        )

        # ==== Asserts ====
        self.global_classifier.run.assert_called_with(message=message, context=self.context, form={})
        assert_action_call(
            action=self.global_action,
            response=self.response,
            message=message,
            context=self.context,
            form={},
        )

    async def test_screen_classification_global_event_overridden_on_screen(self) -> None:
        """
        Переопределённый интент на странице.

        ОР: Вызовется классификатор на странице. Интент не найден.
        Вызовется глобальный классификатор. Отработает обработчик на странице, переопеределяющий данный интент.
        """
        # ==== Mocks ====
        message = self.mocks.message_to_skill(state=AssistantState(screen=self.screen_1_name))
        action_3 = action_mock(payload={"key": "action_3"})
        self.screen_1.add_action(event=self.global_action.event, action=action_3)
        self.context_manager.add_screen(screen=self.screen_1)

        # ==== Run ====
        self.response = await self.context_manager.run(
            event=None,
            message=message,
            context=self.context,
            text_preprocessing_result=self.text_preprocessing_result,
            user=self.mocks.user(message=message),
        )

        # ==== Asserts ====sss
        self.global_classifier.run.assert_called_with(message=message, context=self.context, form={})
        assert_action_call(
            action=action_3,
            response=self.response,
            message=message,
            context=self.context,
            form={},
        )

    async def test_screen_classification_global_event_overridden_on_screen_no_response(self) -> None:
        """
        ## Тест на переопределённый интент на странице c битым экшеном на этот интент.

        ОР: Вызовется классификатор на странице. Интент не найден.
        Вызовется глобальный классификатор. Отработает обработчик на странице, переопеределяющий данный интент,
        Но ответ будет None.
        Вернётся ошибка, ибо обработчик всегда должен возвращать объект наследник Response.
        """
        # ==== Mocks ====
        message = self.mocks.message_to_skill(state=AssistantState(screen=self.screen_1_name))
        action_3 = action_mock()
        action_3.return_value = None

        self.screen_1.add_action(event=self.global_action.event, action=action_3)
        self.context_manager.add_screen(screen=self.screen_1)

        # ==== Run ====
        self.response = await self.context_manager.run(
            event=None,
            message=message,
            context=self.context,
            text_preprocessing_result=self.text_preprocessing_result,
            user=self.mocks.user(message=message),
        )

        # ==== Asserts ====
        self.global_classifier.run.assert_called_with(message=message, context=self.context, form={})
        action_3.assert_called_with(message=message, context=self.context, form={})
        self.assert_error()

    async def test_screen_classification_global_event_no_response(self) -> None:
        """
        ## Тест на битый глобальный обработчик.

        ОР: Вызовется классификатор на странице. Интент не найден.
        Вызовется глобальный классификатор. Отработает глобальный обработчик. Вернёт None.
        Вернётся ошибка, ибо обработчик всегда должен возвращать объект наследник Response.
        """
        # ==== Mocks ====
        classifier = MagicMock()
        classifier.run.return_value = self.broken_global_action_event
        self.context_manager.global_scenario.classifiers = [classifier]
        message = self.mocks.message_to_skill(state=AssistantState(screen=self.screen_2_name))
        self.context_manager.add_screen(screen=self.screen_2)

        # ==== Run ====
        self.response = await self.context_manager.run(
            event=None,
            message=message,
            context=self.context,
            text_preprocessing_result=self.text_preprocessing_result,
            user=self.mocks.user(message=message),
        )

        # ==== Asserts ====
        classifier.run.assert_called_with(message=message, context=self.context, form={})
        classifier.run_legacy.assert_not_called()
        self.broken_global_action.assert_called_with(message=message, context=self.context, form={})
        self.assert_error()

    async def test_screen_local_fallback(self) -> None:
        """
        ## Тест на срабатывание локального фоллбека.

        ОР: Вызовется классификатор: интент не найден.
        Вызовется локальный фоллбек на странице.
        """
        # ==== Mocks ====
        classifier = classifier_mock()
        self.context_manager.global_scenario.classifiers = [classifier]
        message = self.mocks.message_to_skill(state=AssistantState(screen=self.screen_1_name))
        self.context_manager.add_screen(screen=self.screen_1)
        self.context_manager.add_screen(screen=self.screen_2)
        user = self.mocks.user(message=message)

        # ==== Run ====
        self.response = await self.context_manager.run(
            event=None,
            message=message,
            context=self.context,
            text_preprocessing_result=self.text_preprocessing_result,
            user=user,
        )

        # ==== Asserts ====
        classifier.run.assert_called_with(message=message, context=self.context, form={})
        classifier.run_legacy.assert_called_with(
            message=message,
            context=self.context,
            form={},
            text_preprocessing_result=self.text_preprocessing_result,
            user=user,
        )
        self.global_fallback_action.assert_not_called()
        assert_action_call(
            action=self.screen_fallback_action,
            response=self.response,
            message=message,
            context=self.context,
            form={},
        )

    async def test_screen_global_fallback(self) -> None:
        """
        ## Тест на срабатывание глобального фоллбека.

        ОР: Вызовется классификатор: интент не найден. Фоллбек на странице отсутствует.
        Вызовется глобальный фоллбек.
        """
        # ==== Mocks ====
        classifier = classifier_mock()
        self.context_manager.global_scenario.classifiers = [classifier]
        message = self.mocks.message_to_skill(state=AssistantState(screen=self.screen_2_name))
        self.context_manager.add_screen(screen=self.screen_1)
        self.context_manager.add_screen(screen=self.screen_2)
        user = self.mocks.user(message=message)

        # ==== Run ====
        self.response = await self.context_manager.run(
            event=None,
            message=message,
            context=self.context,
            text_preprocessing_result=self.text_preprocessing_result,
            user=user,
        )

        # ==== Asserts ====
        classifier.run.assert_called_with(message=message, context=self.context, form={})
        classifier.run_legacy.assert_called_with(
            message=message,
            context=self.context,
            form={},
            text_preprocessing_result=self.text_preprocessing_result,
            user=user,
        )
        assert_action_call(
            action=self.global_fallback_action,
            response=self.response,
            message=message,
            context=self.context,
            form={},
        )

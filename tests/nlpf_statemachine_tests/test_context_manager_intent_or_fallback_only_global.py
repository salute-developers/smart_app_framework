"""
# Тесты на глобальные экшены и фолбеки.
"""
from unittest.mock import MagicMock

from nlpf_statemachine.example.app.sc.models.context import ExampleContext
from nlpf_statemachine.example.app.user import ExampleUser
from nlpf_statemachine.kit import ContextManager
from nlpf_statemachine.models import Context, NothingFound
from tests.nlpf_statemachine_tests.utils import (
    SMAsyncioTestCase,
    action_mock,
    assert_action_call,
    classifier_mock,
    random_string,
)


class TestScenarioIntentOrFallbackOnlyGlobal(SMAsyncioTestCase):
    """
    # Тесты на отработку классификации глобальных интентов и падение в фолбек.
    """

    CONTEXT_CLASS = ExampleContext
    SMART_KIT_APP_CONFIG = "nlpf_statemachine.example.app_config"
    USER_CLASS = ExampleUser

    def setUp(self) -> None:
        """
        ## Конфигурация базовых параметров перед запуском тестов.
        """
        super(TestScenarioIntentOrFallbackOnlyGlobal, self).setUp()
        self.intent = "HELLO"
        self.stub_event = "STUB"
        self.message = self.mocks.message_to_skill()
        self.context = Context()
        self.user = self.mocks.user(message=self.message)
        self.text_preprocessing_result = self.mocks.text_preprocessing_result()
        self.stub_action = MagicMock(return_value=None)
        self.action = action_mock(payload={"key": "action"})
        self.fallback = action_mock(payload={"key": "screen_fallback"})
        self.context_manager = ContextManager()
        self.context_manager.add_action(event=self.intent, action=self.action)
        self.context_manager.add_action(event=self.stub_event, action=self.stub_action)

    async def test_no_intent_after_classification_without_fallback(self) -> None:
        """
        ## После классификации не определился интент и нет фолбека.

        ОР: ничего не произойдёт, вернётся дефолтный ответ (NothingFound).
        """
        # ==== Mocks ====
        classifier = classifier_mock()
        self.context_manager.add_classifier(classifier=classifier)

        # ==== Run ====
        response = await self.context_manager.run(
            event=None,
            message=self.message,
            context=self.context,
            text_preprocessing_result=self.text_preprocessing_result,
            user=self.user,
        )

        # ==== Asserts ====
        self.action.assert_not_called()
        classifier.run.assert_called_with(message=self.message, context=self.context, form={})
        classifier.run_legacy.assert_called_with(
            message=self.message,
            context=self.context,
            form={},
            text_preprocessing_result=self.text_preprocessing_result,
            user=self.user,
        )
        assert response == NothingFound()

    async def test_no_intent_after_classification_with_fallback(self) -> None:
        """
        ## После классификации не определился интент, но есть фолбек.

        ОР: Сработал фолбек.
        """
        # ==== Mocks ====
        classifier = classifier_mock()
        self.context_manager.add_classifier(classifier=classifier)
        self.context_manager.add_action(event=self.intent, action=self.action)
        self.context_manager.add_action(event=self.stub_event, action=self.stub_action)
        self.context_manager.add_fallback_action(action=self.fallback)

        # ==== Run ====
        response = await self.context_manager.run(
            event=None,
            message=self.message,
            context=self.context,
            text_preprocessing_result=self.text_preprocessing_result,
            user=self.user,
        )

        # ==== Asserts ====
        self.action.assert_not_called()
        classifier.run.assert_called_with(message=self.message, context=self.context, form={})
        classifier.run_legacy.assert_called_with(
            message=self.message,
            context=self.context,
            form={},
            text_preprocessing_result=self.text_preprocessing_result,
            user=self.user,
        )
        assert_action_call(
            action=self.fallback,
            response=response,
            message=self.message,
            context=self.context,
            form={},
        )

    async def test_intent_with_response_with_fallback_and_multi_classifiers(self) -> None:
        """
        ## Тест работы пайплайна классификаторов.

        ОР: Возвращается ответ из обарботчика первого результата классификации, который не None.
        """
        # ==== Mocks ====
        classifier_0 = classifier_mock()
        classifier = classifier_mock(run_legacy_mock=self.action.event)
        classifier_1 = classifier_mock(run_mock=random_string(), run_legacy_mock=random_string())

        self.context_manager.add_classifier(classifier=classifier_0)
        self.context_manager.add_classifier(classifier=classifier)
        self.context_manager.add_classifier(classifier=classifier_1)

        self.context_manager.add_action(event=self.action.event, action=self.action)
        self.context_manager.add_action(event=self.stub_event, action=self.stub_action)
        self.context_manager.add_fallback_action(action=self.fallback)

        # ==== Run ====
        response = await self.context_manager.run(
            event=None,
            message=self.message,
            context=self.context,
            text_preprocessing_result=self.text_preprocessing_result,
            user=self.user,
        )

        # ==== Asserts ====
        classifier.run.assert_called_with(message=self.message, context=self.context, form={})
        classifier.run_legacy.assert_called_with(
            message=self.message,
            context=self.context,
            form={},
            text_preprocessing_result=self.text_preprocessing_result,
            user=self.user,
        )
        classifier.run.assert_called_with(message=self.message, context=self.context, form={})
        classifier.run_legacy.assert_called_with(
            message=self.message,
            context=self.context,
            form={},
            text_preprocessing_result=self.text_preprocessing_result,
            user=self.user,
        )
        classifier_1.run.assert_not_called()
        classifier_1.run_legacy.assert_not_called()
        assert_action_call(
            action=self.action,
            response=response,
            message=self.message,
            context=self.context,
            form={},
        )
        self.stub_action.assert_not_called()
        self.fallback.assert_not_called()

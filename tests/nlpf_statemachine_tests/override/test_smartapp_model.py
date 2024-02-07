"""
# Тесты на nlpf_statemachine.override.smartapp_model.
"""
from unittest.mock import MagicMock, patch

from core.basic_models.actions.command import Command
from nlpf_statemachine.models import BaseMessage, Event, RequestMessageName, Response
from nlpf_statemachine.override import (
    SMDefaultMessageHandler,
    SMDialogueManager,
    SMHandlerCloseApp,
    SMHandlerServerAction,
    SMHandlerTimeout,
    SMUser,
)
from smart_kit.handlers.handler_text import HandlerText
from tests.nlpf_statemachine_tests.utils import AnyObj, SMTestCaseBase, random_string


class TestSmartAppModel(SMTestCaseBase):
    """
    # Тесты на переопределение SmartAppModel.
    """

    SMART_KIT_APP_CONFIG = "nlpf_statemachine.example.app_config"

    def test_get_handler(self) -> None:
        """
        ## Тест на верное определение хэндлера в зависимости от наименования запроса.
        """
        handler = self.core.smart_app_model.get_handler(RequestMessageName.SERVER_ACTION)
        assert isinstance(handler, SMHandlerServerAction)
        assert isinstance(handler.dialogue_manager, SMDialogueManager)

        handler = self.core.smart_app_model.get_handler(RequestMessageName.MESSAGE_TO_SKILL)
        assert isinstance(handler, HandlerText)
        assert isinstance(handler.dialogue_manager, SMDialogueManager)

        handler = self.core.smart_app_model.get_handler(RequestMessageName.RUN_APP)
        assert isinstance(handler, HandlerText)
        assert isinstance(handler.dialogue_manager, SMDialogueManager)

        handler = self.core.smart_app_model.get_handler(RequestMessageName.CLOSE_APP)
        assert isinstance(handler, SMHandlerCloseApp)
        assert isinstance(handler.dialogue_manager, SMDialogueManager)

        handler = self.core.smart_app_model.get_handler("ANY_OTHER_INTEGRATION")
        assert isinstance(handler, SMDefaultMessageHandler)
        assert isinstance(handler.dialogue_manager, SMDialogueManager)

        handler = self.core.smart_app_model.get_handler(Event.LOCAL_TIMEOUT)
        assert isinstance(handler, SMHandlerTimeout)
        assert isinstance(handler.dialogue_manager, SMDialogueManager)

    async def _run_state_machine(self, message: BaseMessage, super_run: MagicMock,
                                 context_manager_run: MagicMock) -> SMUser:
        """
        ## Запуск стейт-машины через smart_app_model.answer.

        Args:
            message (BaseMessage): Сообщение;
            super_run (MagicMock): MagicMock на запуск метода run у соответствующего хэндлера.

        Returns:
            SMUser: Объект User (для других асертов).
        """
        # ==== Mocks ====
        context_manager_run.return_value = Response(messageName="TestResponse")
        super_run.return_value = [Command("command")]
        user = self.mocks.user(message=message)

        # ==== Run ====
        response = await self.core.smart_app_model.answer(message=user.message, user=user)

        # ==== Asserts ====
        assert super_run.called is False
        assert isinstance(response, list)
        assert len(response) == 1
        assert isinstance(response[0], Command)
        assert response[0].name == context_manager_run.return_value.messageName
        return user

    async def _run_nlpf(self, message: BaseMessage, super_run: MagicMock, context_manager_run: MagicMock) -> SMUser:
        """
        ## Запуск NLPF-хэндлеров через smart_app_model.answer.

        Args:
            message (BaseMessage): Сообщение;
            super_run (MagicMock): MagicMock на запуск метода run у соответствующего хэндлера.

        # покрыть тестами, что мы возвращаем результат от super_run!!!
        Returns:
            SMUser: Объект User (для других асертов).
        """
        # ==== Mocks ====
        context_manager_run.return_value = None
        super_run.return_value = [Command("command")]
        user = self.mocks.user(message=message)

        # ==== Run ====
        response = await self.core.smart_app_model.answer(message=user.message, user=user)

        # ==== Asserts ====
        assert super_run.call
        assert response == super_run.return_value
        return user

    @patch("nlpf_statemachine.kit.context_manager.ContextManager.run")
    @patch("smart_kit.handlers.handle_server_action.HandlerServerAction.run")
    async def test_answer_server_action_nlpf(self, super_run: MagicMock, context_manager_run: MagicMock) -> None:
        """
        ## Тест на верный запуск обработки ServerAction (отсутствие ответа от StateMahine).
        """
        message = self.mocks.server_action_message()
        user = await self._run_nlpf(
            message=message,
            super_run=super_run,
            context_manager_run=context_manager_run,
        )
        super_run.assert_called_with(payload=message.payload.model_dump(), user=user)

    @patch("nlpf_statemachine.kit.context_manager.ContextManager.run")
    @patch("smart_kit.handlers.handle_server_action.HandlerServerAction.run")
    async def test_answer_server_action_sm(self, super_run: MagicMock, context_manager_run: MagicMock) -> None:
        """
        ## Тест на верный запуск обработки ServerAction (ответ от StateMachine).
        """
        message = self.mocks.server_action_message()
        user = await self._run_state_machine(
            message=message,
            super_run=super_run,
            context_manager_run=context_manager_run,
        )
        context_manager_run.assert_called_with(
            event=message.payload.server_action.action_id,
            message=message,
            context=user.context_pd,
            text_preprocessing_result=AnyObj(),
            user=user,
        )

    @patch("nlpf_statemachine.kit.context_manager.ContextManager.run")
    @patch("smart_kit.models.dialogue_manager.DialogueManager.run_scenario")
    async def test_answer_message_to_skill_nlpf(self, super_run: MagicMock, context_manager_run: MagicMock) -> None:
        """
        ## Тест на верный запуск обработки MessageToSkill (отсутствие ответа от StateMahine).
        """
        message = self.mocks.message_to_skill()
        user = await self._run_nlpf(
            message=message,
            super_run=super_run,
            context_manager_run=context_manager_run,
        )
        super_run.assert_called_with(
            scen_id=message.payload.intent,
            text_preprocessing_result=AnyObj(),
            user=user,
        )

    @patch("nlpf_statemachine.kit.context_manager.ContextManager.run")
    @patch("smart_kit.models.dialogue_manager.DialogueManager.run_scenario")
    async def test_answer_message_to_skill_sm(self, super_run: MagicMock, context_manager_run: MagicMock) -> None:
        """
        ## Тест на верный запуск обработки MessageToSkill (ответ от StateMachine).
        """
        message = self.mocks.message_to_skill()

        user = await self._run_state_machine(
            message=message,
            super_run=super_run,
            context_manager_run=context_manager_run,
        )
        context_manager_run.assert_called_with(
            event=None,
            message=message,
            context=user.context_pd,
            text_preprocessing_result=AnyObj(),
            user=user,
        )

    @patch("nlpf_statemachine.kit.context_manager.ContextManager.run")
    @patch("smart_kit.models.dialogue_manager.DialogueManager.run_scenario")
    async def test_answer_run_app_nlpf(self, super_run: MagicMock, context_manager_run: MagicMock) -> None:
        """
        ## Тест на верный запуск обработки RunApp (отсутствие ответа от StateMahine).
        """
        message = self.mocks.run_app()
        user = await self._run_nlpf(
            message=message,
            super_run=super_run,
            context_manager_run=context_manager_run,
        )
        super_run.assert_called_with(
            scen_id=message.payload.intent,
            text_preprocessing_result=AnyObj(),
            user=user,
        )

    @patch("nlpf_statemachine.kit.context_manager.ContextManager.run")
    @patch("smart_kit.models.dialogue_manager.DialogueManager.run_scenario")
    async def test_answer_run_app_sm(self, super_run: MagicMock, context_manager_run: MagicMock) -> None:
        """
        ## Тест на верный запуск обработки RunApp (ответ от StateMachine).
        """
        message = self.mocks.run_app()
        await self._run_state_machine(message=message, super_run=super_run, context_manager_run=context_manager_run)

    @patch("nlpf_statemachine.kit.context_manager.ContextManager.run")
    @patch("smart_kit.handlers.handle_close_app.HandlerCloseApp.run")
    async def test_answer_close_app_nlpf(self, super_run: MagicMock, context_manager_run: MagicMock) -> None:
        """
        ## Тест на верный запуск обработки CloseApp (отсутствие ответа от StateMahine).
        """
        message = self.mocks.close_app()
        user = await self._run_nlpf(
            message=message,
            super_run=super_run,
            context_manager_run=context_manager_run,
        )
        super_run.assert_called_with(payload=message.payload.model_dump(), user=user)

    @patch("nlpf_statemachine.kit.context_manager.ContextManager.run")
    @patch("smart_kit.handlers.handle_close_app.HandlerCloseApp.run")
    async def test_answer_close_app_sm(self, super_run: MagicMock, context_manager_run: MagicMock) -> None:
        """
        ## Тест на верный запуск обработки CloseApp (ответ от StateMachine).
        """
        message = self.mocks.close_app()
        user = await self._run_state_machine(
            message=message,
            super_run=super_run,
            context_manager_run=context_manager_run,
        )
        context_manager_run.assert_called_with(
            event=RequestMessageName.CLOSE_APP,
            message=message,
            context=user.context_pd,
            text_preprocessing_result=AnyObj(),
            user=user,
        )

    @patch("nlpf_statemachine.kit.context_manager.ContextManager.run")
    @patch("smart_kit.handlers.handler_timeout.HandlerTimeout.run")
    async def test_answer_timeout_nlpf(self, super_run: MagicMock, context_manager_run: MagicMock) -> None:
        """
        ## Тест на верный запуск обработки LOCAL_TIMEOUT (отсутствие ответа от StateMahine).
        """
        message = self.mocks.local_timeout()
        user = await self._run_nlpf(
            message=message,
            super_run=super_run,
            context_manager_run=context_manager_run,
        )
        super_run.assert_called_with(payload=message.payload, user=user)

    @patch("nlpf_statemachine.kit.context_manager.ContextManager.run")
    @patch("smart_kit.handlers.handler_timeout.HandlerTimeout.run")
    async def test_answer_timeout_sm(self, super_run: MagicMock, context_manager_run: MagicMock) -> None:
        """
        ## Тест на верный запуск обработки LOCAL_TIMEOUT (ответ от StateMachine).
        """
        message = self.mocks.local_timeout()
        user = await self._run_state_machine(
            message=message,
            super_run=super_run,
            context_manager_run=context_manager_run,
        )
        context_manager_run.assert_called_with(
            event=Event.LOCAL_TIMEOUT,
            message=message,
            context=user.context_pd,
            text_preprocessing_result=AnyObj(),
            user=user,
        )

    @patch("nlpf_statemachine.kit.context_manager.ContextManager.run")
    @patch("smart_kit.handlers.handler_base.HandlerBase.run")
    async def test_answer_any_other_message_name_nlpf(self, super_run: MagicMock,
                                                      context_manager_run: MagicMock) -> None:
        """
        ## Тест на верный запуск обработки любого неизвестного сообщения (отсутствие ответа от StateMahine).
        """
        message = self.mocks.local_timeout()
        message.messageName = random_string()
        user = await self._run_nlpf(
            message=message,
            super_run=super_run,
            context_manager_run=context_manager_run,
        )
        super_run.assert_called_with(payload=message.payload, user=user)

    @patch("nlpf_statemachine.kit.context_manager.ContextManager.run")
    @patch("smart_kit.handlers.handler_base.HandlerBase.run")
    async def test_answer_any_other_message_name_sm(self, super_run: MagicMock, context_manager_run: MagicMock) -> None:
        """
        ## Тест на верный запуск обработки любого неизвестного сообщения (ответ от StateMachine).
        """
        message = self.mocks.local_timeout()
        message.messageName = random_string()
        user = await self._run_state_machine(
            message=message,
            super_run=super_run,
            context_manager_run=context_manager_run,
        )
        context_manager_run.assert_called_with(
            event=message.messageName,
            message=message,
            context=user.context_pd,
            text_preprocessing_result=AnyObj(),
            user=user,
        )

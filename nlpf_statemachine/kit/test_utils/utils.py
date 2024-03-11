from datetime import datetime
from typing import List, Optional
from unittest import TestCase
from unittest.mock import MagicMock
from uuid import uuid4

from pydantic import BaseModel

from core.configs.global_constants import CALLBACK_ID_HEADER
from nlpf_statemachine.config import SMConfig
from nlpf_statemachine.kit.context_manager import ContextManager
from nlpf_statemachine.models import (
    AppInfo,
    AssistantMeta,
    AssistantResponsePayload,
    AssistantState,
    Context,
    CurrentApp,
    ErrorResponse,
    IntegrationRequestType,
    IntegrationResponse,
    LocalTimeout,
    Message,
    MessageToSkill,
    MessageToSkillPayload,
    Response,
    ResponseMessageName,
    ServerAction,
    ServerActionMessage,
    ServerActionPayload,
    UUID,
)


class PickleMagicMock(MagicMock):
    """PickleMagicMock это MagicMock который можно сериализовать.

    Создавался для того чтобы можно было сериализовать обьекты,
    в которых есть объекты-mock, например при глубоком копировании
    или выводе в лог (при операции маскирования данных для вывода в лог
    создается глубокая копия)


    '''python
    from pickle import dumps, loads
    from nlpf_statemachine.kit.test_utils.base import PickleMagicMock
    mock = PickleMagicMock()
    dumps(mock)
    '''
    b'.....&nlpf_statemachine.kit.test_utils.base.....PickleMagicMock...'

    Notes:
        При сериализации объекта принадлежащего классу PickleMagicMock
        теряется информация о его внутреннем состоянии.

            >>> mock.run()
            <PickleMagicMock name='mock.run()' id='5810179040'>
            >>> mock.run.call_count
            1
            >>> loaded = loads(dumps(mock))
            >>> loaded.run.call_count
            0
    """

    def __reduce__(self) -> None:
        return PickleMagicMock, ()


class PayloadForTest(AssistantResponsePayload):
    key: str


class TestUtils(TestCase):
    CONTEXT_CLASS = Context

    def setUp(self) -> None:
        self.context = self.CONTEXT_CLASS()
        self.form = {}
        self.text_preprocessing_result = MagicMock()
        self.user = self.mock_user()
        self.context_manager = ContextManager()

    def _get_local_context_class(self) -> None:
        return self.CONTEXT_CLASS.model_fields.get("local").annotation

    def _create_local_context(self) -> None:
        local_context_class = self._get_local_context_class()
        return local_context_class()

    @staticmethod
    def random_string():
        return str(uuid4())

    def init_transaction(self, base_event: str = "DEFAULT_EVENT", transaction_delta_time: float = 2,
                         last_intent=None, screen=None):
        if not last_intent:
            last_intent = self.random_string()
        if not base_event:
            base_event = self.random_string()
        self._set_user_callback(self.user)
        self.context.local = self._create_local_context()
        self.context.local.last_transaction_step_timestamp = datetime.now().timestamp() - transaction_delta_time
        self.context.local.base_event = base_event
        self.context.last_intent = last_intent
        self.context.screen = screen
        # print("INIT", self.context.local)

    # ==== Mocks ====
    def action_mock(self, message_name="TEST", payload=None):
        action = MagicMock()
        action.event = self.random_string()
        action.response_message_name = message_name
        action.response_payload = payload if payload else {}
        action.return_value = Response(
            messageName=message_name,
            payload=payload if payload else AssistantResponsePayload(),
        )
        return action

    @staticmethod
    def action_with_exception_mock(exception=None):
        def function(*args, **kwargs):
            if exception:
                raise exception
            raise Exception("Test Exception")

        action = MagicMock(
            side_effect=function,
        )

        return action

    def action_integration_mock(self, message_name="TEST", payload=None,
                                request_data=None, request_type=IntegrationRequestType.KAFKA):
        action = MagicMock()
        action.event = self.random_string()
        action.response_message_name = message_name
        action.response_payload = payload if payload else {}
        action.request_data = request_data if request_data else {}
        action.request_type = request_type if request_type else {}
        action.return_value = IntegrationResponse(
            messageName=message_name,
            payload=payload if payload else {},
            request_type=request_type,
            request_data=request_data if request_data else {},
        )
        return action

    def _set_user_callback(self, user):
        user.message.callback_id = self.random_string()
        return user.message.callback_id

    def mock_user(self) -> None:
        user = PickleMagicMock()
        user.context_model = self.CONTEXT_CLASS
        user.message = MagicMock()
        user.message.callback_id = None
        user.message.generate_new_callback_id = PickleMagicMock(
            side_effect=lambda: self._set_user_callback(user)
        )

        return user

    @staticmethod
    def classifier_mock(run_mock=None, run_legacy_mock=None):
        classifier = MagicMock()
        classifier.run = MagicMock(return_value=run_mock)
        classifier.run_legacy = MagicMock(return_value=run_legacy_mock)
        return classifier

    # ==== Message Mocks ====
    @staticmethod
    def message_to_skill_mock(text: str = "Привет",
                              intent: str = "HELLO",
                              screen: str = None,
                              tokenized_elements_list: Optional[List] = None,
                              character=None):
        return MessageToSkill(
            payload=MessageToSkillPayload(
                message=Message(
                    original_text=text,
                    tokenized_elements_list=tokenized_elements_list,
                ),
                intent=intent,
                character=character,
                meta=AssistantMeta(
                    current_app=CurrentApp(
                        state=AssistantState(
                            screen=screen,
                        ),
                    ),
                ),
            ),
        )

    def server_action_mock(self, action_id: str = "ACTION_ID", intent: str = "HELLO",
                           screen: Optional[str] = None, parameters: Optional[dict] = None):
        return ServerActionMessage(
            uuid=UUID(
                sub=self.random_string(),
                userId=self.random_string(),
                userChannel=self.random_string(),
            ),
            payload=ServerActionPayload(
                app_info=AppInfo(
                    projectId=self.random_string(),
                    frontendType="WEB_APP",
                ),
                intent=intent,
                server_action=ServerAction(
                    action_id=action_id,
                    parameters=parameters if parameters else None,
                ),
                meta=AssistantMeta(
                    current_app=CurrentApp(
                        state=AssistantState(
                            screen=screen,
                        ),
                    ),
                ),
            ),
        )

    @staticmethod
    def message_timeout_mock(text: str = "Привет", intent: str = "HELLO", screen: str = None):
        return LocalTimeout(
            payload=MessageToSkillPayload(
                message=Message(
                    original_text=text,
                ),
                intent=intent,
                meta=AssistantMeta(
                    current_app=CurrentApp(
                        state=AssistantState(
                            screen=screen,
                        ),
                    ),
                ),
            ),
        )

    # ==== Asserts ====
    @staticmethod
    def assert_single_command(response):
        # assert isinstance(response, list)
        # assert len(response), 1
        # assert isinstance(response[0], Command)
        # assert response
        pass

    def assert_response(self, response, message_name, payload=None):
        # self.assert_single_command(response)
        assert response.messageName == message_name
        if payload:
            assert response.payload == payload

    def assert_action_call(self, action, response, message, context, form):
        action.assert_called_with(message=message, context=context, form=form)
        if isinstance(action.return_value.payload, BaseModel):
            payload = action.return_value.payload.model_dump()
        else:
            payload = action.return_value.payload
        self.assert_response(response=response, message_name=action.return_value.messageName, payload=payload)

    def asserts_not_transaction_end(self) -> None:
        """
        Проверка, что не конец транзакции.

        :param:
        :return:
        """
        self.user.behaviors._add_returned_callback.assert_not_called()
        self.user.behaviors._delete.assert_not_called()
        self.user.behaviors.clear_all.assert_not_called()

    def asserts_on_transaction_end(self, response, intent: str = None):
        """
        Проверка на удаление таймаутов в behavior.

        :param:
        :return:
        """
        if not intent:
            intent = self.context.last_intent

        self.user.behaviors._add_returned_callback.assert_called_with(callback_id=self.user.message.callback_id)
        self.user.behaviors._delete.assert_called_with(callback_id=self.user.message.callback_id)
        self.user.behaviors.clear_all.assert_called_with()

        assert self.context.local.last_transaction_step_timestamp is None
        assert self.context.local.base_event is None
        # assert isinstance(response, list)
        # assert len(response), 1
        # assert isinstance(response[0], Command)
        assert isinstance(response, Response)
        assert response.payload.intent == intent

    def asserts_on_transaction_start(self, response):
        """
        Проверка на установку таймаута в behavior.

        :param response:
        :return:
        """
        self.user.behaviors.add.assert_called_with(
            callback_id=self.user.message.callback_id, behavior_id=SMConfig.default_integration_behaviour_id,
        )
        self.asserts_not_transaction_end()
        # assert isinstance(response, list)
        # assert len(response), 1
        # assert isinstance(response[0], Command)
        assert isinstance(response, Response)
        assert response.request_data.get(CALLBACK_ID_HEADER) == self.user.message.callback_id

    @staticmethod
    def assert_default_error(response):
        # assert isinstance(response, list)
        # assert len(response), 1
        # assert isinstance(response[0], Command)
        # assert response[0].name == ResponseMessageName.ERROR
        assert isinstance(response, ErrorResponse)
        assert response.messageName == ResponseMessageName.ERROR

    @staticmethod
    def assert_called_actions(response):
        # assert isinstance(response, list)
        # assert len(response), 1
        # assert isinstance(response[0], Command)
        # assert response[0].name == ResponseMessageName.ERROR
        assert isinstance(response, ErrorResponse)
        assert response.messageName == ResponseMessageName.ERROR

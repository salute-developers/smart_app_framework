"""
# Тест-кейс для NLPF StateMachine.
"""
import json
from datetime import datetime
from typing import Dict, List, Optional, Union
from unittest import TestCase, IsolatedAsyncioTestCase

from pydantic import BaseModel

from core.configs.global_constants import CALLBACK_ID_HEADER
from core.logging.logger_utils import behaviour_log
from nlpf_statemachine.config import DEFAULT_INTEGRATION_BEHAVIOR_ID
from nlpf_statemachine.const import GLOBAL_NODE_NAME
from nlpf_statemachine.models import (
    Context,
    DoNothing,
    ErrorResponse,
    NothingFound,
    RequestMessageName,
    ResponseMessageName,
)
from nlpf_statemachine.override import SMUser
from .base import random_guid, random_string
from .mocks import BaseMocks, TestsCore


class SMTestCaseBase(TestCase):
    """
    # Базовый класс тест-кейс для фреймворка NLPF StateMachine.
    """

    CONTEXT_CLASS = Context
    SMART_KIT_APP_CONFIG = "app_config"

    def setUp(self) -> None:
        """
        ## Конфигурация базовых параметров перед запуском тестов.
        """
        self.core = TestsCore(smart_kit_app_config=self.SMART_KIT_APP_CONFIG)
        self.mocks = BaseMocks(core=self.core)


class SMAsyncioTestCaseBase(IsolatedAsyncioTestCase):
    """
    # Базовый класс тест-кейс для фреймворка NLPF StateMachine.
    """

    CONTEXT_CLASS = Context
    SMART_KIT_APP_CONFIG = "app_config"

    def setUp(self) -> None:
        """
        ## Конфигурация базовых параметров перед запуском тестов.
        """
        self.core = TestsCore(smart_kit_app_config=self.SMART_KIT_APP_CONFIG)
        self.mocks = BaseMocks(core=self.core)


class SMTestCase(SMTestCaseBase):
    """
    # Основной класс для написания тест-кейсов на фреймворке NLPF StateMachine.

    В отличии от базового тут так же присутствуют типовые ассерты и флоу транзакции.
    """

    USER_CLASS = SMUser

    def setUp(self) -> None:
        """
        ## Конфигурация базовых параметров перед запуском тестов.
        """
        super().setUp()
        self.text_preprocessing_result = None
        self.user = None
        self.context = None
        self.response = None
        self._message_headers = {}
        self._add_callback_in_user = False

    def _get_request_data(self) -> dict:
        """
        ## Извлечение request_data из ответа.
        """
        if isinstance(self.response.request_data, dict):
            return self.response.request_data
        elif isinstance(self.response.request_data, BaseModel):
            return self.response.request_data.dict()
        return {}

    def init(
            self,
            context: Optional[Union[Dict, Context]] = None,
            transaction_started: bool = False,
            base_event: Optional[str] = None,
            transaction_duration: float = 2,
            last_event: Optional[str] = None,
            last_intent: Optional[str] = None,
            last_screen: Optional[str] = None,
            last_response_message_name: Optional[str] = None,
    ) -> None:
        """
        ## Инициализация всех системных объектов для запуска ContextManager.

        Args:
            context:
            transaction_started:
            base_event:
            transaction_duration:
            last_event:
            last_intent:
            last_screen:
            last_response_message_name:

        Returns:
            None.
        """
        if not isinstance(context, self.CONTEXT_CLASS):
            if isinstance(context, dict):
                self.context = self.CONTEXT_CLASS(**context)
            elif isinstance(context, BaseModel):
                self.context = self.CONTEXT_CLASS(**context.dict())
            else:
                self.context = self.CONTEXT_CLASS()

        if transaction_started:
            if not base_event:
                base_event = random_string()
            self.context.local.base_event = base_event
            self.context.local.last_transaction_step_timestamp = datetime.now().timestamp() - transaction_duration
            self._message_headers = {CALLBACK_ID_HEADER: random_guid().encode()}
            self._add_callback_in_user = True

        if not self.context.last_event:
            self.context.last_event = last_event
        if not self.context.last_intent:
            self.context.last_intent = last_intent
        if not self.context.last_screen:
            self.context.last_screen = last_screen
        if not self.context.last_response_message_name:
            self.context.last_response_message_name = last_response_message_name

    def _set_request_data_to_message_headers(self, request_data: Dict) -> None:
        if not request_data:
            return
        if isinstance(request_data, BaseModel):
            request_data = request_data.dict()
        for key, value in request_data.items():
            if isinstance(value, str):
                self._message_headers[key] = value.encode()

    async def run_context_manager(
            self,
            message: Union[Dict, BaseModel],
            event: Optional[str] = None,
            text_preprocessing_result: Optional[List] = None,
    ) -> None:
        """
        ## Запуск ContextManager.

        Ответ записывается в self.response.

        Args:
            message:
            event:
            text_preprocessing_result:

        Returns:
            None.
        """
        message_dict = dict(message)
        if message_dict.get("messageName") == RequestMessageName.MESSAGE_TO_SKILL and not text_preprocessing_result:
            self.text_preprocessing_result = self.mocks.text_preprocessing_result(payload=message_dict.get("payload"))

        if self.context:
            db_data = json.dumps({"context_pd": self.context.dict(exclude_none=True)})
        else:
            db_data = "{}"
            behaviour_log("Method init is not called.", level="WARNING")

        self.user = self.mocks.user(
            message=message,
            headers=self._message_headers,
            db_data=db_data,
            user_cls=self.USER_CLASS,
        )

        if self._add_callback_in_user and self._message_headers.get(CALLBACK_ID_HEADER):
            self.user.behaviors.add(
                callback_id=self._message_headers.get(CALLBACK_ID_HEADER).decode(),
                behavior_id=DEFAULT_INTEGRATION_BEHAVIOR_ID,
            )
            self._add_callback_in_user = False

        self.response = await self.core.context_manager.run(
            event=event,
            message=self.user.message_pd,
            context=self.user.context_pd,
            user=self.user,
            text_preprocessing_result=self.text_preprocessing_result,
        )

        self.context = self.user.context_pd
        self._set_request_data_to_message_headers(request_data=self.response.request_data)

    async def run_context_manager_init(
            self,
            message: Union[Dict, BaseModel],
            event: Optional[str] = None,
            text_preprocessing_result: Optional[List] = None,
            context: Optional[Union[Dict, Context]] = None,
            transaction_started: bool = False,
            base_event: Optional[str] = None,
            transaction_duration: float = 2,
            last_event: Optional[str] = None,
            last_intent: Optional[str] = None,
            last_screen: Optional[str] = None,
            last_response_message_name: Optional[str] = None,
    ) -> None:
        """
        ## Инициализация и запуск ContextManager.

        Ответ записывается в self.response.

        Args:
            message:
            event:
            text_preprocessing_result:
            context:
            transaction_started:
            base_event:
            transaction_duration:
            last_event:
            last_intent:
            last_screen:
            last_response_message_name:

        Returns:
            None.
        """
        self.init(
            context=context,
            transaction_started=transaction_started,
            base_event=base_event,
            transaction_duration=transaction_duration,
            last_event=last_event,
            last_intent=last_intent,
            last_screen=last_screen,
            last_response_message_name=last_response_message_name,
        )
        await self.run_context_manager(
            event=event,
            message=message,
            text_preprocessing_result=text_preprocessing_result,
        )

    # ======== Asserts ========
    def assert_timeout_exists(self) -> None:
        """
        ## Проверка на наличие установленного таймаута.
        """
        request_data = self._get_request_data()
        assert len(self.user.behaviors._callbacks) > 0
        assert CALLBACK_ID_HEADER in request_data
        assert self.user.behaviors.has_callback(callback_id=self.response.request_data.app_callback_id)

    def assert_transaction_started(self) -> None:
        """
        ## Проверка, что транзакция началась.
        """
        self.assert_timeout_exists()
        assert self.context.local.base_event is not None
        assert self.response.debug_info.transaction_finished is False

    def assert_transaction_continue(self) -> None:
        """
        ## Проверка, что транзакция продолжается.
        """
        self.assert_timeout_exists()
        callback_ids = self.user.behaviors.get_returned_callbacks()
        assert self.user.message.callback_id in callback_ids
        assert self.response.debug_info.transaction_finished is False

    def assert_transaction_finished(self) -> None:
        """
        ## Проверка, что транзакция завершена.
        """
        # timeouts = self.user.behaviors.get_behavior_timeouts()
        request_data = self._get_request_data()
        # assert len(timeouts) == 0
        assert len(self.user.behaviors._callbacks) == 0
        assert self.response.debug_info.transaction_finished is True
        assert CALLBACK_ID_HEADER not in request_data

    def assert_no_response(self) -> None:
        """
        ## Проверка на отсутствие ответа от экшенов.
        """
        if self.core.context_manager.run_smart_app_framework_base_kit:
            assert self.response is None
        else:
            assert isinstance(self.response, NothingFound) or isinstance(self.response, DoNothing)

    def assert_debug_info(
            self,
            called_event: str,
            called_action: str,
            called_scenario: Optional[str] = GLOBAL_NODE_NAME,
            call_history_size: int = 1,
            finished_transaction: bool = True,
            base_event: Optional[str] = None,
            static_code: Optional[str] = None,
    ) -> None:
        """
        ## Проверка параметров debug_info.

        Args:
            called_event (str): Событие, которое было распознано в текущем запросе;
            called_action (str): Action, который был вызван;
            called_scenario (str, optional): Scenario, который был вызван;
            call_history_size (int, optional): Размер транзакции на текущий момент, default: 1;
            finished_transaction (bool, optional): Флаг окончания транзакции, default: True;
            base_event (str, optional): Базовое событие в транзакции, default: None;
            static_code (str, optional): Код ответа в статике (при использовании StaticStorage).

        Returns:
            None.
        """
        assert self.response.debug_info.base_event == base_event
        assert self.response.debug_info.transaction_finished == finished_transaction
        assert len(self.response.debug_info.call_history) == call_history_size
        assert self.response.debug_info.call_history[-1].event == called_event
        assert self.response.debug_info.call_history[-1].action == called_action
        assert self.response.debug_info.call_history[-1].scenario == called_scenario
        if static_code:
            assert self.response.debug_info.static_code == static_code

    def assert_error(self, message_name: Optional[str] = None) -> None:
        """
        ## Проверка на ошибку в ответ.

        Args:
            message_name (str, optional): Наименование ответа. (по дефолту: ERROR)

        Returns:
            None.
        """
        assert isinstance(self.response, ErrorResponse)
        if not message_name:
            assert self.response.messageName == ResponseMessageName.ERROR
        else:
            assert self.response.messageName == message_name


class SMAsyncioTestCase(SMAsyncioTestCaseBase):
    """
    # Основной класс для написания тест-кейсов на фреймворке NLPF StateMachine.

    В отличии от базового тут так же присутствуют типовые ассерты и флоу транзакции.
    """

    USER_CLASS = SMUser

    def setUp(self) -> None:
        """
        ## Конфигурация базовых параметров перед запуском тестов.
        """
        super().setUp()
        self.text_preprocessing_result = None
        self.user = None
        self.context = None
        self.response = None
        self._message_headers = {}
        self._add_callback_in_user = False

    def _get_request_data(self) -> dict:
        """
        ## Извлечение request_data из ответа.
        """
        if isinstance(self.response.request_data, dict):
            return self.response.request_data
        elif isinstance(self.response.request_data, BaseModel):
            return self.response.request_data.dict()
        return {}

    def init(
            self,
            context: Optional[Union[Dict, Context]] = None,
            transaction_started: bool = False,
            base_event: Optional[str] = None,
            transaction_duration: float = 2,
            last_event: Optional[str] = None,
            last_intent: Optional[str] = None,
            last_screen: Optional[str] = None,
            last_response_message_name: Optional[str] = None,
    ) -> None:
        """
        ## Инициализация всех системных объектов для запуска ContextManager.

        Args:
            context:
            transaction_started:
            base_event:
            transaction_duration:
            last_event:
            last_intent:
            last_screen:
            last_response_message_name:

        Returns:
            None.
        """
        if not isinstance(context, self.CONTEXT_CLASS):
            if isinstance(context, dict):
                self.context = self.CONTEXT_CLASS(**context)
            elif isinstance(context, BaseModel):
                self.context = self.CONTEXT_CLASS(**context.dict())
            else:
                self.context = self.CONTEXT_CLASS()

        if transaction_started:
            if not base_event:
                base_event = random_string()
            self.context.local.base_event = base_event
            self.context.local.last_transaction_step_timestamp = datetime.now().timestamp() - transaction_duration
            self._message_headers = {CALLBACK_ID_HEADER: random_guid().encode()}
            self._add_callback_in_user = True

        if not self.context.last_event:
            self.context.last_event = last_event
        if not self.context.last_intent:
            self.context.last_intent = last_intent
        if not self.context.last_screen:
            self.context.last_screen = last_screen
        if not self.context.last_response_message_name:
            self.context.last_response_message_name = last_response_message_name

    def _set_request_data_to_message_headers(self, request_data: Dict) -> None:
        if not request_data:
            return
        if isinstance(request_data, BaseModel):
            request_data = request_data.dict()
        for key, value in request_data.items():
            if isinstance(value, str):
                self._message_headers[key] = value.encode()

    async def run_context_manager(
            self,
            message: Union[Dict, BaseModel],
            event: Optional[str] = None,
            text_preprocessing_result: Optional[List] = None,
    ) -> None:
        """
        ## Запуск ContextManager.

        Ответ записывается в self.response.

        Args:
            message:
            event:
            text_preprocessing_result:

        Returns:
            None.
        """
        message_dict = dict(message)
        if message_dict.get("messageName") == RequestMessageName.MESSAGE_TO_SKILL and not text_preprocessing_result:
            self.text_preprocessing_result = self.mocks.text_preprocessing_result(payload=message_dict.get("payload"))

        if self.context:
            db_data = json.dumps({"context_pd": self.context.dict(exclude_none=True)})
        else:
            db_data = "{}"
            behaviour_log("Method init is not called.", level="WARNING")

        self.user = self.mocks.user(
            message=message,
            headers=self._message_headers,
            db_data=db_data,
            user_cls=self.USER_CLASS,
        )

        if self._add_callback_in_user and self._message_headers.get(CALLBACK_ID_HEADER):
            self.user.behaviors.add(
                callback_id=self._message_headers.get(CALLBACK_ID_HEADER).decode(),
                behavior_id=DEFAULT_INTEGRATION_BEHAVIOR_ID,
            )
            self._add_callback_in_user = False

        self.response = await self.core.context_manager.run(
            event=event,
            message=self.user.message_pd,
            context=self.user.context_pd,
            user=self.user,
            text_preprocessing_result=self.text_preprocessing_result,
        )

        self.context = self.user.context_pd
        self._set_request_data_to_message_headers(request_data=self.response.request_data)

    async def run_context_manager_init(
            self,
            message: Union[Dict, BaseModel],
            event: Optional[str] = None,
            text_preprocessing_result: Optional[List] = None,
            context: Optional[Union[Dict, Context]] = None,
            transaction_started: bool = False,
            base_event: Optional[str] = None,
            transaction_duration: float = 2,
            last_event: Optional[str] = None,
            last_intent: Optional[str] = None,
            last_screen: Optional[str] = None,
            last_response_message_name: Optional[str] = None,
    ) -> None:
        """
        ## Инициализация и запуск ContextManager.

        Ответ записывается в self.response.

        Args:
            message:
            event:
            text_preprocessing_result:
            context:
            transaction_started:
            base_event:
            transaction_duration:
            last_event:
            last_intent:
            last_screen:
            last_response_message_name:

        Returns:
            None.
        """
        self.init(
            context=context,
            transaction_started=transaction_started,
            base_event=base_event,
            transaction_duration=transaction_duration,
            last_event=last_event,
            last_intent=last_intent,
            last_screen=last_screen,
            last_response_message_name=last_response_message_name,
        )
        await self.run_context_manager(
            event=event,
            message=message,
            text_preprocessing_result=text_preprocessing_result,
        )

    # ======== Asserts ========
    def assert_timeout_exists(self) -> None:
        """
        ## Проверка на наличие установленного таймаута.
        """
        request_data = self._get_request_data()
        assert len(self.user.behaviors._callbacks) > 0
        assert CALLBACK_ID_HEADER in request_data
        assert self.user.behaviors.has_callback(callback_id=self.response.request_data.app_callback_id)

    def assert_transaction_started(self) -> None:
        """
        ## Проверка, что транзакция началась.
        """
        self.assert_timeout_exists()
        assert self.context.local.base_event is not None
        assert self.response.debug_info.transaction_finished is False

    def assert_transaction_continue(self) -> None:
        """
        ## Проверка, что транзакция продолжается.
        """
        self.assert_timeout_exists()
        callback_ids = self.user.behaviors.get_returned_callbacks()
        assert self.user.message.callback_id in callback_ids
        assert self.response.debug_info.transaction_finished is False

    def assert_transaction_finished(self) -> None:
        """
        ## Проверка, что транзакция завершена.
        """
        # timeouts = self.user.behaviors.get_behavior_timeouts()
        request_data = self._get_request_data()
        # assert len(timeouts) == 0
        assert len(self.user.behaviors._callbacks) == 0
        assert self.response.debug_info.transaction_finished is True
        assert CALLBACK_ID_HEADER not in request_data

    def assert_no_response(self) -> None:
        """
        ## Проверка на отсутствие ответа от экшенов.
        """
        if self.core.context_manager.run_smart_app_framework_base_kit:
            assert self.response is None
        else:
            assert isinstance(self.response, NothingFound) or isinstance(self.response, DoNothing)

    def assert_debug_info(
            self,
            called_event: str,
            called_action: str,
            called_scenario: Optional[str] = GLOBAL_NODE_NAME,
            call_history_size: int = 1,
            finished_transaction: bool = True,
            base_event: Optional[str] = None,
            static_code: Optional[str] = None,
    ) -> None:
        """
        ## Проверка параметров debug_info.

        Args:
            called_event (str): Событие, которое было распознано в текущем запросе;
            called_action (str): Action, который был вызван;
            called_scenario (str, optional): Scenario, который был вызван;
            call_history_size (int, optional): Размер транзакции на текущий момент, default: 1;
            finished_transaction (bool, optional): Флаг окончания транзакции, default: True;
            base_event (str, optional): Базовое событие в транзакции, default: None;
            static_code (str, optional): Код ответа в статике (при использовании StaticStorage).

        Returns:
            None.
        """
        assert self.response.debug_info.base_event == base_event
        assert self.response.debug_info.transaction_finished == finished_transaction
        assert len(self.response.debug_info.call_history) == call_history_size
        assert self.response.debug_info.call_history[-1].event == called_event
        assert self.response.debug_info.call_history[-1].action == called_action
        assert self.response.debug_info.call_history[-1].scenario == called_scenario
        if static_code:
            assert self.response.debug_info.static_code == static_code

    def assert_error(self, message_name: Optional[str] = None) -> None:
        """
        ## Проверка на ошибку в ответ.

        Args:
            message_name (str, optional): Наименование ответа. (по дефолту: ERROR)

        Returns:
            None.
        """
        assert isinstance(self.response, ErrorResponse)
        if not message_name:
            assert self.response.messageName == ResponseMessageName.ERROR
        else:
            assert self.response.messageName == message_name

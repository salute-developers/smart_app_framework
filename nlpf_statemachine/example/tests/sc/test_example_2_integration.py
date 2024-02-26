"""
# Пример тестирования работы транзакции.
"""
from nlpf_statemachine.example.app.sc.enums.integration_message_names import (
    IntegrationRequestMessageName, IntegrationResponseMessageName,
)
from nlpf_statemachine.example.app.sc.example_2_integration import GET_DATA
from nlpf_statemachine.example.app.sc.models.context import ExampleContext
from nlpf_statemachine.example.app.sc.models.integration import GetDataResponse
from nlpf_statemachine.example.app.user import ExampleUser
from nlpf_statemachine.models import Event, ResponseMessageName
from tests.nlpf_statemachine_tests.utils import SMTestCase, random_string


class TestGetData(SMTestCase):
    """
    # Пример тестирования транзакции.

    Тесты на работу сценария получения данных.
    """

    CONTEXT_CLASS = ExampleContext
    SMART_KIT_APP_CONFIG = "nlpf_statemachine.example.app_config"
    USER_CLASS = ExampleUser

    def assert_request(self) -> None:
        """
        # Проверка параметров запроса в интеграцию.
        """
        assert self.response.messageName == IntegrationRequestMessageName.GENERATE_DATA
        assert self.response.payload.uuid.sub == self.message.uuid.sub
        assert self.response.payload.uuid.userChannel == self.message.uuid.userChannel
        assert self.response.payload.uuid.userId == self.message.uuid.userId
        assert self.response.payload.projectId == self.message.payload.app_info.projectId

    def setUp(self) -> None:
        """
        # Конфигурация базовых параметров перед запуском тестов.
        """
        super().setUp()
        self.data_response = GetDataResponse(**{
            "payload": {
                "data": {
                    "data": random_string(length=30),
                },
            },
        })
        self.message = self.mocks.server_action_message(action_id=GET_DATA)
        self.call_history_size = 0

    async def start_integration(self) -> None:
        """
        # Запуск транзакции получения данных.
        """
        self.call_history_size += 1
        await self.run_context_manager_init(
            event=GET_DATA,
            message=self.message,
        )
        assert self.context.last_event == GET_DATA
        assert self.context.last_response_message_name == IntegrationRequestMessageName.GENERATE_DATA

        self.assert_request()
        self.assert_transaction_started()
        self.assert_debug_info(
            finished_transaction=False,
            called_event=GET_DATA,
            called_action="IntegrationExample.get_data_action",
        )

    async def finish_integration_success(self) -> None:
        """
        # Интеграция ответил успешно.

        В таком случае: транзакция завершается, пользователю возвращаются данные.
        """
        self.call_history_size += 1
        await self.run_context_manager(
            event=IntegrationResponseMessageName.GENERATE_DATA,
            message=self.data_response,
        )
        assert self.context.last_event == IntegrationResponseMessageName.GENERATE_DATA
        assert self.context.last_response_message_name == ResponseMessageName.ANSWER_TO_USER

        self.assert_transaction_finished()
        self.assert_debug_info(
            call_history_size=self.call_history_size,
            called_event=IntegrationResponseMessageName.GENERATE_DATA,
            called_action="IntegrationExample.get_data_success_action",
            base_event=GET_DATA,
        )
        assert self.response.messageName == ResponseMessageName.ANSWER_TO_USER

    async def finish_integration_timeout(self, finished_transaction: bool) -> None:
        """
        # Интеграция ответилв таймаутом.
        """
        self.call_history_size += 1
        await self.run_context_manager(
            event=Event.LOCAL_TIMEOUT,
            message=self.message,
        )
        assert self.context.last_event == Event.LOCAL_TIMEOUT

        if finished_transaction:
            assert self.context.last_response_message_name == ResponseMessageName.ANSWER_TO_USER
            assert self.response.messageName == ResponseMessageName.ANSWER_TO_USER
            self.assert_transaction_finished()
            self.assert_debug_info(
                call_history_size=self.call_history_size,
                called_event=Event.LOCAL_TIMEOUT,
                called_action="IntegrationExample.get_data_timeout_action",
                base_event=GET_DATA,
                finished_transaction=finished_transaction,
            )

        else:
            assert self.context.last_response_message_name == IntegrationRequestMessageName.GENERATE_DATA
            self.assert_request()
            self.assert_transaction_continue()
            self.assert_debug_info(
                call_history_size=self.call_history_size,
                called_event=Event.LOCAL_TIMEOUT,
                called_action="IntegrationExample.get_data_timeout_action",
                base_event=GET_DATA,
                finished_transaction=finished_transaction,
            )

    async def test_get_data_server_action_success(self) -> None:
        """
        # Успешный кейс.

        Схема: * DP -> Scenario -> Integration -> Scenario (SUCCESS) -> DP *

        Интеграция отвечает успешно, транзакция завершается.
        """
        # Request 1. DP -> Scenario -> Integration
        await self.start_integration()

        # Request 2. Integration -> Scenario (SUCCESS) -> DP
        await self.finish_integration_success()

    async def test_get_data_server_action_timeout_once(self) -> None:
        """
        # Первый запрос таймаутит.

        Схема: * DP -> Scenario -> Integration -> Scenario (TIMEOUT) -> Integration -> Scenario (SUCCESS) -> DP *

        Интеграция не отвечает.
        Перезапрашиваем 1 раз, получаем успешный ответ, транзакция завершается.
        """
        # Request 1. DP -> Scenario -> Integration
        await self.start_integration()

        # Request 2. Integration -> Scenario (TIMEOUT) -> Integration
        await self.finish_integration_timeout(finished_transaction=False)

        # Request 3. Integration -> Scenario (SUCCESS) -> DP
        await self.finish_integration_success()

    async def test_get_data_server_action_timeout_multiple(self) -> None:
        """
        # Интеграция всегда таймаутит.

        Схема: * DP -> Scenario -> Integration -> Scenario (TIMEOUT) -> Integration -> Scenario (TIMEOUT) -> DP *

        Интеграция не отвечает.
        Перезапрашиваем 1 раз, получаем таймаут оба раза, транзакция завершается неуспешно.
        """
        # Request 1. DP -> Scenario -> Integration
        await self.start_integration()

        # Request 2. Integration -> Scenario (TIMEOUT) -> Integration
        await self.finish_integration_timeout(finished_transaction=False)

        # Request 3. Integration -> Scenario (TIMEOUT) -> DP
        await self.finish_integration_timeout(finished_transaction=True)

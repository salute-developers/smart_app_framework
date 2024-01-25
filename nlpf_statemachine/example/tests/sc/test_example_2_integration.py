"""
# Пример тестирования работы транзакции.
"""
from random import randint

from nlpf_statemachine.example.app.sc.enums.integration_message_names import (
    IntegrationRequestMessageName, IntegrationResponseMessageName,
)
from nlpf_statemachine.example.app.sc.example_2_integration import GET_TOKEN
from nlpf_statemachine.example.app.sc.models.context import ExampleContext
from nlpf_statemachine.example.app.sc.models.token_service_integration import GetTokenResponse
from nlpf_statemachine.example.app.user import ExampleUser
from nlpf_statemachine.models import Event, ResponseMessageName
from tests.nlpf_statemachine_tests.utils import SMTestCase, random_string


class TestGetToken(SMTestCase):
    """
    # Пример тестирования транзакции.

    Тесты на работу сценария получения токена.
    """

    CONTEXT_CLASS = ExampleContext
    SMART_KIT_APP_CONFIG = "nlpf_statemachine.example.app_config"
    USER_CLASS = ExampleUser

    def assert_token_service_request(self) -> None:
        """
        # Проверка параметров запроса в токен-сервис.
        """
        assert self.response.messageName == IntegrationRequestMessageName.GENERATE_TOKEN
        assert self.response.payload.uuid.sub == self.message.uuid.sub
        assert self.response.payload.uuid.userChannel == self.message.uuid.userChannel
        assert self.response.payload.uuid.userId == self.message.uuid.userId
        assert self.response.payload.projectId == self.message.payload.app_info.projectId

    def setUp(self) -> None:
        """
        # Конфигурация базовых параметров перед запуском тестов.
        """
        super().setUp()
        self.token_service_response = GetTokenResponse(**{
            "payload": {
                "data": {
                    "accessToken": random_string(length=30),
                    "expiresIn": randint(0, 100000000),
                },
            },
        })
        self.message = self.mocks.server_action_message(action_id=GET_TOKEN)
        self.call_history_size = 0

    async def start_token_service_integration(self) -> None:
        """
        # Запуск транзакции получения токена.
        """
        self.call_history_size += 1
        await self.run_context_manager_init(
            event=GET_TOKEN,
            message=self.message,
        )
        assert self.context.last_event == GET_TOKEN
        assert self.context.last_response_message_name == IntegrationRequestMessageName.GENERATE_TOKEN

        self.assert_token_service_request()
        self.assert_transaction_started()
        self.assert_debug_info(
            finished_transaction=False,
            called_event=GET_TOKEN,
            called_action="IntegrationExample.get_token_action",
        )

    async def finish_token_service_integration_success(self) -> None:
        """
        # Токен-Сервис ответил успешно.

        В таком случае: транзакция завершается, пользователю возвращается токен.
        """
        self.call_history_size += 1
        await self.run_context_manager(
            event=IntegrationResponseMessageName.GENERATE_TOKEN,
            message=self.token_service_response,
        )
        assert self.context.last_event == IntegrationResponseMessageName.GENERATE_TOKEN
        assert self.context.last_response_message_name == ResponseMessageName.ANSWER_TO_USER

        self.assert_transaction_finished()
        self.assert_debug_info(
            call_history_size=self.call_history_size,
            called_event=IntegrationResponseMessageName.GENERATE_TOKEN,
            called_action="IntegrationExample.get_token_success_action",
            base_event=GET_TOKEN,
        )
        assert self.response.messageName == ResponseMessageName.ANSWER_TO_USER

    async def finish_token_service_integration_timeout(self, finished_transaction: bool) -> None:
        """
        # Токен-Сервис ответил таймаутом.
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
                called_action="IntegrationExample.get_token_timeout_action",
                base_event=GET_TOKEN,
                finished_transaction=finished_transaction,
            )

        else:
            assert self.context.last_response_message_name == IntegrationRequestMessageName.GENERATE_TOKEN
            self.assert_token_service_request()
            self.assert_transaction_continue()
            self.assert_debug_info(
                call_history_size=self.call_history_size,
                called_event=Event.LOCAL_TIMEOUT,
                called_action="IntegrationExample.get_token_timeout_action",
                base_event=GET_TOKEN,
                finished_transaction=finished_transaction,
            )

    async def test_get_token_server_action_success(self) -> None:
        """
        # Успешный кейс.

        Схема: * DP -> Scenario -> TokenService -> Scenario (SUCCESS) -> DP *

        Токен-сервис отвечает успешно, транзакция завершается.
        """
        # Request 1. DP -> Scenario -> TokenService
        await self.start_token_service_integration()

        # Request 2. TokenService -> Scenario (SUCCESS) -> DP
        await self.finish_token_service_integration_success()

    async def test_get_token_server_action_timeout_once(self) -> None:
        """
        # Первый запрос таймаутит.

        Схема: * DP -> Scenario -> TokenService -> Scenario (TIMEOUT) -> TokenService -> Scenario (SUCCESS) -> DP *

        Токен-сервис не отвечает.
        Перезапрашиваем 1 раз, получаем успешный ответ, транзакция завершается.
        """
        # Request 1. DP -> Scenario -> TokenService
        await self.start_token_service_integration()

        # Request 2. TokenService -> Scenario (TIMEOUT) -> TokenService
        await self.finish_token_service_integration_timeout(finished_transaction=False)

        # Request 3. TokenService -> Scenario (SUCCESS) -> DP
        await self.finish_token_service_integration_success()

    async def test_get_token_server_action_timeout_multiple(self) -> None:
        """
        # Токен-Сервис всегда таймаутит.

        Схема: * DP -> Scenario -> TokenService -> Scenario (TIMEOUT) -> TokenService -> Scenario (TIMEOUT) -> DP *

        Токен-сервис не отвечает.
        Перезапрашиваем 1 раз, получаем таймаут оба раза, транзакция завершается неуспешно.
        """
        # Request 1. DP -> Scenario -> TokenService
        await self.start_token_service_integration()

        # Request 2. TokenService -> Scenario (TIMEOUT) -> TokenService
        await self.finish_token_service_integration_timeout(finished_transaction=False)

        # Request 3. TokenService -> Scenario (TIMEOUT) -> DP
        await self.finish_token_service_integration_timeout(finished_transaction=True)

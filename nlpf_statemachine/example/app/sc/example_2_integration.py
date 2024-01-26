"""
# Сценарий получения токена.

1. Пример простой интеграции с TokenService.
2. Пример run_app, где так же используется интеграция с токен-сервисом.
"""
from nlpf_statemachine.example.app.sc.enums.integration_message_names import (
    IntegrationRequestMessageName, IntegrationResponseMessageName,
)
from nlpf_statemachine.example.app.sc.models.context import ExampleContext
from nlpf_statemachine.example.app.sc.models.token_service_integration import GetTokenPayload, GetTokenRequest
from nlpf_statemachine.kit import Scenario
from nlpf_statemachine.models import AnswerToUser, AssistantMessage, AssistantResponsePayload, Response

# 1. Определяем необходимые параметры.
INTEGRATION_TOPIC_KEY = "food_source"
GET_TOKEN = "GET_TOKEN"

# 2. Инициализируем сценарий для глобального сценария и отдельную страницу.
scenario = Scenario("IntegrationExample")


# 3. Добавляем классификаторы.


# 4. Описываем общие методы.
def get_ihapi_token(message: AssistantMessage) -> GetTokenRequest:
    """
    # Метод для генерации запроса в токен-сервис.

    Args:
        message (AssistantMessage): Запрос от ассистента

    Returns:
        GetTokenRequest: Запрос в токен-сервис.
    """
    return GetTokenRequest(
        payload=GetTokenPayload(
            uuid=message.uuid,
            projectId=message.payload.app_info.projectId,
        ),
        request_data={
            "topic_key": INTEGRATION_TOPIC_KEY,
        },
    )


# 5. Добавим обработчики событии и тамйаута.
@scenario.on_event(event=GET_TOKEN)
def get_token_action(message: AssistantMessage, context: ExampleContext) -> Response:
    r"""
    # Получение токена от TokenService.

    **Событие:**  `GET_TOKEN`.

    **Базовое событие:** Отсутствует (начинает транзакцию по получению токена).

    Интеграция с токен-сервисом происходит через кафку.

    ## Возможные следующие шаги транзакции
    1. Таймаут: `get_token_timeout_action`;
    2. Успешный ответ от интеграции: `get_token_success_action` \n
        (событие: `IntegrationResponseMessageName.GENERATE_TOKEN`);

    Args:
        message (AssistantMessage): Запрос от ассистента
        context (ExampleContext): Контекст запроса от ассистента

    Returns:
        GetTokenRequest: Запрос на получение токена в токен-сервис.
    """
    context.local.retry_index = 0
    return get_ihapi_token(message)


@scenario.on_timeout(request_name=IntegrationRequestMessageName.GENERATE_TOKEN)
def get_token_timeout_action(message: AssistantMessage, context: ExampleContext) -> Response:
    """
    # Таймаут при запросе токена из TokenService.

    **Событие:**  Таймаут на запрос `IntegrationRequestMessageName.GENERATE_TOKEN`.

    **Базовое событие:** Любое.

    Делаем 1 попытку перезапросить токен, в случае не успеха возвращаем голосовой ответ с ошибкой
    и заканчиваем транзакцию.

    Args:
        message (AssistantMessageИмя): Запрос от ассистента
        context (ExampleContext): Контекст запроса от ассистента

    Returns:
        GetTokenRequest: Запрос на получение токена в токен-сервис.
        AnswerToUser: Сообщение об ошибке.
    """
    if context.local.retry_index < 1:
        context.local.retry_index += 1
        return get_ihapi_token(message)

    return AnswerToUser(
        payload=AssistantResponsePayload(
            pronounceText="К сожалению, произошёл таймаут получения данных от токен-сервиса",
        ),
    )


@scenario.on_event(event=IntegrationResponseMessageName.GENERATE_TOKEN, base_event=GET_TOKEN)
def get_token_success_action() -> Response:
    """
    # Успешный ответа от TokenService в случае GET_TOKEN.

    **Событие:** `IntegrationResponseMessageName.GENERATE_TOKEN`.

    **Базовое событие:** `ServerAction.GET_TOKEN`.

    В случае успешного овтета отдаём пользователю голосовй ответ и заканчиваем транзакцию.

    Returns:
        AnswerToUser: Сообщение об успешном ответе.
    """
    return AnswerToUser(
        payload=AssistantResponsePayload(
            pronounceText="Токен получен! Я пришёл от GET_TOKEN",
        ),
    )

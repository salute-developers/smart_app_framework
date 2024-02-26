"""
# Сценарий получения данных.

1. Пример простой интеграции.
2. Пример run_app, где так же используется интеграция.
"""
from nlpf_statemachine.example.app.sc.enums.integration_message_names import (
    IntegrationRequestMessageName, IntegrationResponseMessageName,
)
from nlpf_statemachine.example.app.sc.models.context import ExampleContext
from nlpf_statemachine.example.app.sc.models.integration import GetDataPayload, GetDataRequest
from nlpf_statemachine.kit import Scenario
from nlpf_statemachine.models import AnswerToUser, AssistantMessage, AssistantResponsePayload, Response

# 1. Определяем необходимые параметры.
INTEGRATION_TOPIC_KEY = "food_source"
GET_DATA = "GET_DATA"

# 2. Инициализируем сценарий для глобального сценария и отдельную страницу.
scenario = Scenario("IntegrationExample")


# 3. Добавляем классификаторы.


# 4. Описываем общие методы.
def get_ihapi_data(message: AssistantMessage) -> GetDataRequest:
    """
    # Метод для генерации запроса в интеграцию.

    Args:
        message (AssistantMessage): Запрос от ассистента

    Returns:
        GetDataRequest: Запрос в интеграцию.
    """
    return GetDataRequest(
        payload=GetDataPayload(
            uuid=message.uuid,
            project=message.payload.app_info.projectId,
        ),
        request_data={
            "topic_key": INTEGRATION_TOPIC_KEY,
        },
    )


# 5. Добавим обработчики событии и тамйаута.
@scenario.on_event(event=GET_DATA)
def get_data_action(message: AssistantMessage, context: ExampleContext) -> Response:
    r"""
    # Получение данных от интеграции.

    **Событие:**  `GET_DATA`.

    **Базовое событие:** Отсутствует (начинает транзакцию по получению данных).

    Интеграция происходит через кафку.

    ## Возможные следующие шаги транзакции
    1. Таймаут: `get_data_timeout_action`;
    2. Успешный ответ от интеграции: `get_data_success_action` \n
        (событие: `IntegrationResponseMessageName.GENERATE_DATA`);

    Args:
        message (AssistantMessage): Запрос от ассистента
        context (ExampleContext): Контекст запроса от ассистента

    Returns:
        GetDataRequest: Запрос на получение данны в интеграцию.
    """
    context.local.retry_index = 0
    return get_ihapi_data(message)


@scenario.on_timeout(request_name=IntegrationRequestMessageName.GENERATE_DATA)
def get_data_timeout_action(message: AssistantMessage, context: ExampleContext) -> Response:
    """
    # Таймаут при запросе данных.

    **Событие:**  Таймаут на запрос `IntegrationRequestMessageName.GENERATE_DATA`.

    **Базовое событие:** Любое.

    Делаем 1 попытку перезапросить данные, в случае не успеха возвращаем голосовой ответ с ошибкой
    и заканчиваем транзакцию.

    Args:
        message (AssistantMessageИмя): Запрос от ассистента
        context (ExampleContext): Контекст запроса от ассистента

    Returns:
        GetDataRequest: Запрос на получение данных в интеграцию.
        AnswerToUser: Сообщение об ошибке.
    """
    if context.local.retry_index < 1:
        context.local.retry_index += 1
        return get_ihapi_data(message)

    return AnswerToUser(
        payload=AssistantResponsePayload(
            pronounceText="К сожалению, произошёл таймаут получения данных от интеграции",
        ),
    )


@scenario.on_event(event=IntegrationResponseMessageName.GENERATE_DATA, base_event=GET_DATA)
def get_data_success_action() -> Response:
    """
    # Успешный ответ.

    **Событие:** `IntegrationResponseMessageName.GENERATE_DATA`.

    **Базовое событие:** `GET_DATA`.

    В случае успешного овтета отдаём пользователю голосовй ответ и заканчиваем транзакцию.

    Returns:
        AnswerToUser: Сообщение об успешном ответе.
    """
    return AnswerToUser(
        payload=AssistantResponsePayload(
            pronounceText="Данные получены! Я пришёл от GET_DATA",
        ),
    )

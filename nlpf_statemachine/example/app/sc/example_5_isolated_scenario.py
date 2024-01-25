"""
# Пример изолированного сценария --- запуск аппа.

В данном примере изолированный сценарий НЕ возвращает ответ,
а получает токен и передаёт управление дальше - в стейт-машину.

На запуске аппа необходимо сделать следующее:
1. Запустить
1. Пример простой интеграции с TokenService.
2. Пример run_app, где так же используется интеграция с токен-сервисом.
"""
from typing import Optional

from nlpf_statemachine.example.app.sc.enums.integration_message_names import IntegrationResponseMessageName
from nlpf_statemachine.example.app.sc.example_2_integration import get_ihapi_token
from nlpf_statemachine.example.app.sc.models.context import ExampleContext
from nlpf_statemachine.example.app.sc.models.token_service_integration import GetTokenResponse
from nlpf_statemachine.kit import ConstClassifier, Scenario
from nlpf_statemachine.models import AssistantMessage, Response

# 1. Определяем необходимые параметры.
RUN_APP = "RUN_APP"

# 2. Инициализируем изолированный сценарий запуска и классификатор с постоянным значением: RUN_APP.
scenario = Scenario("RunAppExample")
scenario.add_classifier(ConstClassifier(value=RUN_APP))


# 3. Определим условие на запуск.
def run_app_condition(message: AssistantMessage) -> bool:
    """
    ## Условие на запуск изолированного процесса.

    Args:
        message (BaseMessage): Сообщение;

    Returns:
        bool: true --- процесс запустится, false --- нет.
    """
    try:
        return message.payload.new_session
    except Exception:
        return False


# 4. Добавим обработчики событии и тамйаута.
@scenario.on_event(event=RUN_APP)
def run_app(message: AssistantMessage, context: ExampleContext) -> Response:
    r"""
    # Запуск приложения.

    **Событие:**  `RUN_APP`.

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


@scenario.on_event(event=IntegrationResponseMessageName.GENERATE_TOKEN, base_event=RUN_APP)
def get_token_success_action(message: GetTokenResponse, context: ExampleContext) -> Optional[Response]:
    """
    # Успешный ответа от TokenService в случае RUN_APP.

    **Событие:** `IntegrationResponseMessageName.GENERATE_TOKEN`.

    **Базовое событие:** `ServerAction.GET_TOKEN`.

    В случае успешного овтета сохраняем токен в контекст и возвращаем управление в стейт-машину.

    Returns:
        None.
    """
    context.local.ihapi_token = message.payload.data
    return

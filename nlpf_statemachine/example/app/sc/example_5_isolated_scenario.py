"""
# Пример изолированного сценария --- запуск аппа.

В данном примере изолированный сценарий НЕ возвращает ответ,
а получает данные и передаёт управление дальше - в стейт-машину.

На запуске аппа необходимо сделать следующее:
1. Запустить
1. Пример простой интеграции.
2. Пример run_app, где так же используется интеграция.
"""
from typing import Optional

from nlpf_statemachine.example.app.sc.enums.integration_message_names import IntegrationResponseMessageName
from nlpf_statemachine.example.app.scenario_utils import get_integration_data
from nlpf_statemachine.example.app.sc.models.context import ExampleContext
from nlpf_statemachine.example.app.sc.models.integration import GetDataResponse
from nlpf_statemachine.kit import ConstClassifier, Scenario
from nlpf_statemachine.models import AssistantMessage, Response

# 1. Определяем необходимые параметры.
RUN_APP = "RUN_APP"

# 2. Инициализируем изолированный сценарий запуска и классификатор с постоянным значением: RUN_APP.
scenario = Scenario("RunAppExample")
scenario.add_classifier(ConstClassifier(value=RUN_APP))


# 3. Определяем условие на запуск.
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


# 4. Добавляем обработчики событий и таймаута.
@scenario.on_event(event=RUN_APP)
def run_app(message: AssistantMessage, context: ExampleContext) -> Response:
    r"""
    # Запуск приложения.

    **Событие:** `RUN_APP`.

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
        GetDataRequest: Запрос на получение данных из интеграции.
    """
    context.local.retry_index = 0
    return get_integration_data(message)


@scenario.on_event(event=IntegrationResponseMessageName.GENERATE_DATA, base_event=RUN_APP)
def get_data_success_action(message: GetDataResponse, context: ExampleContext) -> Optional[Response]:
    """
    # Успешный ответа от интеграции в случае RUN_APP.

    **Событие:** `IntegrationResponseMessageName.GENERATE_DATA`.

    **Базовое событие:** `RUN_APP`.

    В случае успешного овтета сохраняем данные в контекст и возвращаем управление в стейт-машину.

    Returns:
        None.
    """
    context.local.data = message.payload.data
    return

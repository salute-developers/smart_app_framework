"""
# Пример пре-процесса с использованием изолированого сценария, возвращающего эхо-ответ.
"""

from nlpf_statemachine.example.app.sc.models.pre_process_message import (
    CustomPreProcessMessage, CustomPreProcessMessagePayload,
)
from nlpf_statemachine.kit import ConstClassifier, Scenario
from nlpf_statemachine.models import AnswerToUser, AssistantMessage, AssistantResponsePayload, Response

# 1. Определяем необходимые параметры.
EVENT = "CONST_EVENT"

# 2. Инициализируем изолированный сценарий запуска и классификатор с постоянным значением: RUN_APP.
scenario = Scenario("PreProcessExample")
scenario.add_classifier(ConstClassifier(value=EVENT))


# 3. Определяем условие на запуск.
def pre_process_condition(message: AssistantMessage) -> bool:
    """
    ## Условие на запуск изолированного процесса.

    Args:
        message (BaseMessage): Сообщение;

    Returns:
        bool: тип сообщения CustomPreProcessMessage --- процесс запустится, иначе --- нет.
    """
    return isinstance(message, CustomPreProcessMessage)


# 4. Добавляем обработчики событий и таймаута.
@scenario.on_event(event=EVENT)
def action(payload: CustomPreProcessMessagePayload) -> Response:
    """
    ## Обработка сгенерированного в pre_process сообщения в виде эхо.

    В данном кейсе у нас запрос подкладывается непосредственно в `payload.incoming_message` , откуда мы его и достаём.

    Args:
        payload (AssistantMessage): Запрос от ассистента, который лежит в payload нашего сообщения.

    Returns:
        Response: Эхо-ответ ассистента.
    """
    return AnswerToUser(
        payload=AssistantResponsePayload(
            pronounceText=payload.incoming_message.payload.message.original_text,
        ),
    )

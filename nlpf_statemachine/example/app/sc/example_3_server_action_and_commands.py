"""
# Пример работы с сервер-экшенами и командами для фронта.
"""
from nlpf_statemachine.example.app.sc.commands import custom_command
from nlpf_statemachine.kit import Scenario
from nlpf_statemachine.models import AnswerToUser, ServerAction

# 1. Объявляем сервер-экшен, который хотим обработать.
SERVER_ACTION_ID = "SERVER_ACTION_ID"


# 2. Инициализируем сценарий
scenario = Scenario("CommandOnServerActionExample")


# 3. Добавляем обработчик события (сервер-экшена).
@scenario.on_event(event=SERVER_ACTION_ID)
def example_server_action_handler(server_action: ServerAction) -> AnswerToUser:
    """
    # Пример обработки сервер-экшена и генерации команды.

    **Событие:** `SERVER_ACTION_ID`.

    В данном случае транзакция 1-шаговая.

    Параметры сервер-экшена по дефолту сформированы в виде dict, ожидаем, что нам придут 2 поля field_1 и field_2.

    Args:
        server_action (ServerAction): Сервер-экшен из запроса.

    Returns:
        AnswerToUser: Ответ с командой CustomCommand.
    """
    parameters = server_action.parameters or {}
    field_1 = parameters.get("field_1")
    field_2 = parameters.get("field_2")

    response = AnswerToUser()
    if field_1 and field_2:
        response.payload.items.append(
            custom_command(field_1=field_1, field_2=field_2),
        )
    return response

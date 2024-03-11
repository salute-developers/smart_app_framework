"""
# Основные запросы (ServerAction и MessageToSkill).
"""

from pydantic import Field

from nlpf_statemachine.models.enums import RequestMessageName
from nlpf_statemachine.models.message.protocol import AssistantMessage, MessageToSkillPayload, ServerActionPayload


class MessageToSkill(AssistantMessage):
    """
    # Описание модели MessageToSkill.

    Основное сообщение для смартапа.
    """

    messageName: str = RequestMessageName.MESSAGE_TO_SKILL
    """Тип запроса: MESSAGE_TO_SKILL."""
    payload: MessageToSkillPayload = Field(default_factory=MessageToSkillPayload)
    """Коллекция, в которой передается дополнительная информация."""


class ServerActionMessage(AssistantMessage):
    """
    # Описание модели ServerActionMessage.

    С помощью сообщения SERVER_ACTION вы можете получать информацию о действиях пользователя в приложении,
    например, нажатии кнопок. Вы также можете отслеживать фоновые действия полноэкранных приложений.
    """

    messageName: str = RequestMessageName.SERVER_ACTION
    """Тип запроса: SERVER_ACTION."""
    payload: ServerActionPayload = Field(default_factory=ServerActionPayload)
    """Коллекция, в которой передается дополнительная информация."""


class RunApp(ServerActionMessage):
    """
    # Описание модели RunApp.

    Сообщение на запуск аппа.
    """

    messageName: str = RequestMessageName.RUN_APP
    """Тип запроса: RUN_APP."""


class CloseApp(MessageToSkill):
    """
    # Описание модели CloseApp.

    Пользователь закрыл апп, в апп прилетает оповещение.
    """

    messageName: str = RequestMessageName.CLOSE_APP
    """Тип запроса: CLOSE_APP."""

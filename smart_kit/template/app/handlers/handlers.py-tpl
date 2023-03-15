from typing import List, Dict, Any

from core.basic_models.actions.command import Command
from smart_kit.handlers.handler_base import HandlerBase
from scenarios.user.user_model import User


class CustomHandler(HandlerBase):
    """Обработчик некоторого типа входящих сообщений

    Для сопоставления типа сообщения обработчику, добавьте такую пару в CustomModel.additional_handlers. По умолчанию,
    данный обработчик сопоставлен типу сообщения "CUSTOM_MESSAGE_NAME".
    """
    async def run(self, payload: Dict[str, Any], user: User) -> List[Command]:
        commands = await super().run(payload, user)
        return commands

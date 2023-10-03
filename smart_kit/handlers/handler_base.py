# coding: utf-8
from typing import List, Dict, Any, Optional

from core.basic_models.actions.command import Command
from core.monitoring.monitoring import monitoring
from scenarios.user.user_model import User


class HandlerBase:
    TOPIC_KEY = "template_app"
    KAFKA_KEY = "main"

    def __init__(self, app_name: str):
        self.app_name = app_name

    async def run(self, payload: Dict[str, Any], user: User) -> Optional[List[Command]]:
        # отправка события о входящем сообщении в систему мониторинга
        monitoring.counter_incoming(self.app_name, user.message.message_name, self.__class__.__name__,
                                    user, app_info=user.message.app_info)
        return []

from typing import List, Any, Dict

from core.basic_models.actions.command import Command
from core.logging.logger_utils import log
from scenarios.user.user_model import User

from smart_kit.handlers.handler_base import HandlerBase
from smart_kit.names.field import PROFILE_DATA, STATUS_CODE, CODE, GEO


class HandlerTakeProfileData(HandlerBase):
    SUCCESS_CODE = 1

    def run(self, payload: Dict[str, Any], user: User) -> List[Command]:
        commands = super().run(payload, user)
        log(f"{self.__class__.__name__} started", user)

        if payload.get(STATUS_CODE, {}).get(CODE) == self.SUCCESS_CODE:
            commands.extend(user.behaviors.success(user.message.callback_id))
            user.variables.set("smart_geo", payload.get(PROFILE_DATA, {}).get(GEO))
        else:
            commands.extend(user.behaviors.fail(user.message.callback_id))
        return commands

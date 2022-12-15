from typing import List

from core.basic_models.actions.command import Command
from core.logging.logger_utils import log
from scenarios.user.user_model import User

from smart_kit.handlers.handler_base import HandlerBase
from smart_kit.names.field import STATUS_CODE, CODE, PERMITTED_ACTIONS


class HandlerTakeRuntimePermissions(HandlerBase):
    SUCCESS_CODE = 1

    def run(self, payload, user: User) -> List[Command]:
        commands = super().run(payload, user)
        log(f"{self.__class__.__name__} started", user)
        if payload.get(STATUS_CODE, {}).get(CODE) == self.SUCCESS_CODE:
            commands.extend(user.behaviors.success(user.message.callback_id))
            user.variables.set("permitted_actions", payload.get(PERMITTED_ACTIONS, []))
        else:
            commands.extend(user.behaviors.fail(user.message.callback_id))
        user.variables.set("take_runtime_permissions_status_code", payload.get(STATUS_CODE, {}))
        return commands

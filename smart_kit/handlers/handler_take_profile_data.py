from typing import Any, Dict, AsyncGenerator

from core.basic_models.actions.command import Command
from core.logging.logger_utils import log
from scenarios.user.user_model import User

from smart_kit.handlers.handler_base import HandlerBase
from smart_kit.names.field import PROFILE_DATA, STATUS_CODE, CODE, GEO


class HandlerTakeProfileData(HandlerBase):
    SUCCESS_CODE = 1

    async def run(self, payload: Dict[str, Any], user: User) -> AsyncGenerator[Command, None]:
        async for command in super().run(payload, user):
            yield command
        log(f"{self.__class__.__name__} started", user)

        if payload.get(STATUS_CODE, {}).get(CODE) == self.SUCCESS_CODE:
            async for command in user.behaviors.success(user.message.callback_id):
                yield command
            user.variables.set("smart_geo", payload.get(PROFILE_DATA, {}).get(GEO))
        else:
            async for command in user.behaviors.fail(user.message.callback_id):
                yield command

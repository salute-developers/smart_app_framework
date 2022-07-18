from core.logging.logger_utils import log
from scenarios.user.user_model import User

from smart_kit.handlers.handler_base import HandlerBase
from smart_kit.names.field import PROFILE_DATA, STATUS_CODE, CODE, GEO


class HandlerTakeProfileData(HandlerBase):
    SUCCESS_CODE = 1

    async def run(self, payload, user: User):
        await super().run(payload, user)
        log(f"{self.__class__.__name__} started", user)

        commands = await user.behaviors.fail(user.message.callback_id)
        if payload.get(STATUS_CODE, {}).get(CODE) == self.SUCCESS_CODE:
            commands = await user.behaviors.success(user.message.callback_id)
            user.variables.set("smart_geo", payload.get(PROFILE_DATA, {}).get(GEO))
        return commands

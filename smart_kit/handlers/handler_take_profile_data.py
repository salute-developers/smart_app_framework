from core.logging.logger_utils import log
from core.names.field import MESSAGE
from core.text_preprocessing.preprocessing_result import TextPreprocessingResult
from scenarios.user.user_model import User

from smart_kit.handlers.handler_base import HandlerBase
from smart_kit.names.field import PROFILE_DATA, STATUS_CODE, CODE, GEO


class HandlerTakeProfileData(HandlerBase):
    SUCCESS_CODE = 1

    def run(self, payload, user: User):
        super().run(payload, user)
        log(f"{self.__class__.__name__} started", user)

        text_preprocessing_result = TextPreprocessingResult(payload.get(MESSAGE, {}))
        commands = user.behaviors.fail(user.message.callback_id)
        if payload.get(STATUS_CODE, {}).get(CODE) == self.SUCCESS_CODE:
            commands = user.behaviors.success(user.message.callback_id)
            user.variables.set("smart_geo", payload.get(PROFILE_DATA, {}).get(GEO))
        return commands

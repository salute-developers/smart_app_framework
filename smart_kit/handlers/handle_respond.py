from time import time
from typing import List, Optional, Dict, Any

from core.basic_models.actions.command import Command
from core.logging.logger_utils import log

from core.text_preprocessing.preprocessing_result import TextPreprocessingResult
import scenarios.logging.logger_constants as log_const
from scenarios.user.user_model import User

from smart_kit.handlers.handler_base import HandlerBase
from smart_kit.names.action_params_names import TO_MESSAGE_NAME, SEND_TIMESTAMP
from core.monitoring.monitoring import monitoring


class HandlerRespond(HandlerBase):
    handler_name = "HandlerRespond"

    def __init__(self, app_name: str, action_name: Optional[str] = None):
        super().__init__(app_name)
        self._action_name = action_name

    def get_action_name(self, payload: Dict[str, Any], user: User):
        return self._action_name

    def get_action_params(self, payload: Dict[str, Any], user: User):
        callback_id = user.message.callback_id
        return user.behaviors.get_callback_action_params(callback_id)

    async def run(self, payload: Dict[str, Any], user: User) -> List[Command]:
        commands = await super().run(payload, user)
        callback_id = user.message.callback_id
        action_params = self.get_action_params(payload, user)
        action_name = self.get_action_name(payload, user)
        params = {
            log_const.KEY_NAME: "process_time",
            log_const.BEHAVIOR_CALLBACK_ID_VALUE: callback_id,
            "process_time": self.get_processing_time(user),
            "action_name": action_name,
            "surface": user.message.device.surface,
        }

        if user.behaviors.has_callback(callback_id):
            action_params = self.get_action_params(payload, user)
            params["to_message_name"] = action_params.get(TO_MESSAGE_NAME)
            log("HandlerRespond with action %(action_name)s started respond on %(to_message_name)s", user, params)
        else:
            log("HandlerRespond with action %(action_name)s started without callback", user, params)

        monitoring.counter_incoming(self.app_name, user.message.message_name, self.__class__.__name__, user)

        text_preprocessing_result = TextPreprocessingResult.from_payload(payload)

        if payload.get("message"):
            params = {
                log_const.KEY_NAME: log_const.NORMALIZED_TEXT_VALUE,
                "normalized_text": str(text_preprocessing_result.raw),
            }
            log("text preprocessing result: '%(normalized_text)s'", user, params, level="DEBUG")

        action = user.descriptions["external_actions"][action_name]
        commands.extend(await action.run(user, text_preprocessing_result, action_params) or [])
        return commands

    @staticmethod
    def get_processing_time(user: User):
        callback_id = user.message.callback_id
        process_time = None
        callback_params = user.behaviors.get_callback_action_params(callback_id) or {}
        if SEND_TIMESTAMP in callback_params:
            process_time = time() - callback_params[SEND_TIMESTAMP]
            process_time = int(process_time * 1000)
        return process_time

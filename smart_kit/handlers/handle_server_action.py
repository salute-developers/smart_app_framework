from typing import List, Dict, Any, Optional

import scenarios.logging.logger_constants as log_const
from core.basic_models.actions.command import Command

from core.names.field import SERVER_ACTION
from core.logging.logger_utils import log
from core.text_preprocessing.preprocessing_result import TextPreprocessingResult
from core.utils.pickle_copy import pickle_deepcopy
from scenarios.user.user_model import User

from smart_kit.handlers.handler_base import HandlerBase
from core.monitoring.monitoring import monitoring


class HandlerServerAction(HandlerBase):
    handler_name = "HandlerServerAction"

    def __init__(self, app_name: str, action_name: Optional[str] = None):
        super().__init__(app_name)
        self._action_name = action_name

    def get_action_name(self, payload: Dict[str, Any], user: User):
        return payload[SERVER_ACTION]["action_id"]

    def get_action_params(self, payload: Dict[str, Any]):
        return payload[SERVER_ACTION].get("parameters", {})

    def run(self, payload: Dict[str, Any], user: User) -> List[Command]:
        commands = super().run(payload, user)
        action_params = pickle_deepcopy(self.get_action_params(payload))
        params = {log_const.KEY_NAME: "handling_server_action",
                  "server_action_params": str(action_params),
                  "server_action_id": self.get_action_name(payload, user)}
        log("HandlerServerAction %(server_action_id)s started", user, params)

        app_info = user.message.app_info
        monitoring.counter_incoming(self.app_name, user.message.message_name, self.__class__.__name__,
                                    user, app_info=app_info)

        action_id = self.get_action_name(payload, user)
        action = user.descriptions["external_actions"][action_id]
        commands.extend(action.run(user, TextPreprocessingResult({}), action_params) or [])
        return commands

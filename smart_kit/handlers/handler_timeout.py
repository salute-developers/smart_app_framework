# coding: utf-8
from typing import List, Dict, Any

from core.basic_models.actions.command import Command
from core.logging.logger_utils import log
import scenarios.logging.logger_constants as log_const
from scenarios.user.user_model import User
from smart_kit.handlers.handler_base import HandlerBase
from smart_kit.message.app_info import AppInfo
from core.names.field import APP_INFO
from smart_kit.names.message_names import RUN_APP, MESSAGE_TO_SKILL, SERVER_ACTION
from core.monitoring.monitoring import monitoring


class HandlerTimeout(HandlerBase):

    async def run(self, payload: Dict[str, Any], user: User) -> List[Command]:
        commands = []
        callback_id = user.message.callback_id
        if user.behaviors.has_callback(callback_id):
            params = {log_const.KEY_NAME: "handling_timeout"}
            log("TimeoutHandler started", user, params)
            action_params = user.behaviors.get_callback_action_params(callback_id)
            if action_params:
                app_info = None
                for original_message_name in [MESSAGE_TO_SKILL, SERVER_ACTION, RUN_APP]:
                    if original_message_name in action_params:
                        app_info = AppInfo(action_params[original_message_name].get(APP_INFO, {}))
                        break

                monitoring.counter_incoming(self.app_name, user.message.message_name, self.__class__.__name__,
                                            user, app_info=app_info)

            callback_id = user.message.callback_id
            commands.extend(await user.behaviors.timeout(callback_id))
        return commands

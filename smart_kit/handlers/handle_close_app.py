from typing import List, Any, Dict

from core.basic_models.actions.command import Command
from core.logging.logger_utils import log
from core.text_preprocessing.preprocessing_result import TextPreprocessingResult
import scenarios.logging.logger_constants as log_const
from scenarios.actions.action import ClearCurrentScenarioAction
from scenarios.user.user_model import User

from smart_kit.handlers.handler_base import HandlerBase


class HandlerCloseApp(HandlerBase):
    def __init__(self, app_name: str):
        super().__init__(app_name)
        self._clear_current_scenario = ClearCurrentScenarioAction()

    def run(self, payload: Dict[str, Any], user: User) -> List[Command]:
        commands = super().run(payload, user)
        text_preprocessing_result = TextPreprocessingResult.from_payload(payload)
        params = {
            log_const.KEY_NAME: "HandlerCloseApp"
        }
        self._clear_current_scenario.run(user, text_preprocessing_result)
        if payload.get("message"):
            params["tpr_str"] = str(text_preprocessing_result.raw)
        log("HandlerCloseApp with text preprocessing result", user, params)
        return commands

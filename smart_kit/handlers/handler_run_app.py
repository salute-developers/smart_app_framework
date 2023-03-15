from typing import Dict, Any, List

import scenarios.logging.logger_constants as log_const
from core.basic_models.actions.command import Command
from core.logging.logger_utils import log
from core.text_preprocessing.preprocessing_result import TextPreprocessingResult
from scenarios.user.user_model import User

from smart_kit.handlers.handler_base import HandlerBase
from smart_kit.models.dialogue_manager import DialogueManager


class HandlerRunApp(HandlerBase):
    def __init__(self, app_name: str, dialogue_manager: DialogueManager):
        super().__init__(app_name)
        log(
            f"{self.__class__.__name__}.__init__ started.", params={log_const.KEY_NAME: log_const.STARTUP_VALUE}
        )
        self.dialogue_manager = dialogue_manager
        log(
            f"{self.__class__.__name__}.__init__ finished.", params={log_const.KEY_NAME: log_const.STARTUP_VALUE}
        )

    async def run(self, payload: Dict[str, Any], user: User) -> List[Command]:
        commands = await super().run(payload, user)

        params = {log_const.KEY_NAME: "handling_run_app"}
        log(f"{self.__class__.__name__}.run started", user, params)

        commands.extend(await self._handle_base(user))
        return commands

    async def _handle_base(self, user: User) -> List[Command]:
        answer, is_answer_found = await self.dialogue_manager.run(TextPreprocessingResult({}), user)
        return answer or []

from typing import Dict, Any, AsyncGenerator

import scenarios.logging.logger_constants as log_const
from core.basic_models.actions.command import Command
from core.logging.logger_utils import log
from core.text_preprocessing.preprocessing_result import TextPreprocessingResult
from scenarios.user.user_model import User

from smart_kit.handlers.handler_base import HandlerBase
from smart_kit.models.dialogue_manager import DialogueManager


class HandlerText(HandlerBase):
    def __init__(self, app_name: str, dialogue_manager: DialogueManager):
        super().__init__(app_name)
        log(
            f"{self.__class__.__name__}.__init__ started.", params={log_const.KEY_NAME: log_const.STARTUP_VALUE}
        )
        self.dialogue_manager = dialogue_manager
        log(
            f"{self.__class__.__name__}.__init__ finished.", params={log_const.KEY_NAME: log_const.STARTUP_VALUE}
        )

    async def run(self, payload: Dict[str, Any], user: User) -> AsyncGenerator[Command, None]:
        async for command in super().run(payload, user):
            yield command

        text_preprocessing_result = TextPreprocessingResult.from_payload(payload)

        params = {
            log_const.KEY_NAME: log_const.NORMALIZED_TEXT_VALUE,
            "normalized_text": str(text_preprocessing_result.raw),
        }
        log("text preprocessing result: '%(normalized_text)s'", user, params)

        async for command in self._handle_base(text_preprocessing_result, user):
            yield command

    async def _handle_base(self, text_preprocessing_result: TextPreprocessingResult,
                           user: User) -> AsyncGenerator[Command, None]:
        async for command in self.dialogue_manager.run(text_preprocessing_result, user):
            yield command

# coding: utf-

import scenarios.logging.logger_constants as log_const
from core.logging.logger_utils import log
from core.text_preprocessing.preprocessing_result import TextPreprocessingResult

from smart_kit.handlers.handler_base import HandlerBase


class HandlerRunApp(HandlerBase):

    def __init__(self, app_name, dialogue_manager):
        super().__init__(app_name)
        log(
            f"{self.__class__.__name__}.__init__ started.", params={log_const.KEY_NAME: log_const.STARTUP_VALUE}
        )
        self.dialogue_manager = dialogue_manager
        log(
            f"{self.__class__.__name__}.__init__ finished.", params={log_const.KEY_NAME: log_const.STARTUP_VALUE}
        )

    def run(self, payload, user):
        super().run(payload, user)

        params = {log_const.KEY_NAME: "handling_run_app"}
        log(f"{self.__class__.__name__}.run started", user, params)

        answer = self._handle_base(user)
        return answer

    def _handle_base(self, user):
        answer, is_answer_found = self.dialogue_manager.run(TextPreprocessingResult({}), user)
        return answer or []

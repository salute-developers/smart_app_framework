from typing import Dict, Any, Optional, Union, AsyncGenerator

from core.basic_models.actions.basic_actions import Action
from core.basic_models.actions.string_actions import StringAction
from core.basic_models.actions.command import Command
from core.text_preprocessing.base import BaseTextPreprocessingResult

from scenarios.user.user_model import User

from smart_kit.names.message_names import NOTHING_FOUND


class NothingFoundAction(Action):
    version: Optional[int]
    id: Optional[str]

    def __init__(self, items: Dict[str, Any] = None, id: Optional[str] = None):
        super().__init__(items, id)
        self._action = StringAction({"command": NOTHING_FOUND})

    async def run(self, user: User, text_preprocessing_result: BaseTextPreprocessingResult,
                  params: Optional[Dict[str, Union[str, float, int]]] = None) -> AsyncGenerator[Command, None]:
        async for command in self._action.run(user, text_preprocessing_result, params=params):
            yield command

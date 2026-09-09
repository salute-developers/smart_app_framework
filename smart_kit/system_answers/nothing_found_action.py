from __future__ import annotations

from typing import Any

from core.basic_models.actions.basic_actions import Action
from core.basic_models.actions.string_actions import StringAction
from core.basic_models.actions.command import Command
from core.text_preprocessing.base import BaseTextPreprocessingResult

from scenarios.user.user_model import User

from smart_kit.names.message_names import NOTHING_FOUND


class NothingFoundAction(Action):
    version: int | None
    id: str | None

    def __init__(self, items: dict[str, Any] = None, id: str | None = None):
        super().__init__(items, id)
        self._action = StringAction({"command": NOTHING_FOUND})

    async def run(self, user: User, text_preprocessing_result: BaseTextPreprocessingResult,
                  params: dict[str, str | float | int] | None = None) -> list[Command]:
        commands = []
        commands.extend(await self._action.run(user, text_preprocessing_result, params=params) or [])
        return commands

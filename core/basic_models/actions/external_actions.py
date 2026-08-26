from __future__ import annotations

from typing import Any

from core.basic_models.actions.basic_actions import CommandAction, Action
from core.basic_models.actions.basic_actions import action_factory
from core.basic_models.actions.command import Command
from core.descriptions.smart_updatable_descriptions_items import SmartUpdatableDescriptionsItems
from core.model.base_user import BaseUser
from core.text_preprocessing.base import BaseTextPreprocessingResult


class ExternalActions(SmartUpdatableDescriptionsItems):
    def __init__(self, items: dict[str, Any]):
        super().__init__(action_factory, items)


class ExternalAction(CommandAction):
    version: int | None

    def __init__(self, items: dict[str, Any], id: str | None = None):
        super().__init__(items, id)
        self._action_key: str = items["action"]

    async def run(self, user: BaseUser, text_preprocessing_result: BaseTextPreprocessingResult,
                  params: dict[str, str | float | int] | None = None) -> list[Command]:
        action: Action = user.descriptions["external_actions"][self._action_key]
        commands = await action.run(user, text_preprocessing_result, params)
        return commands

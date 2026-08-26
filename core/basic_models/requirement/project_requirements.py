from __future__ import annotations

from typing import Any

from core.text_preprocessing.base import BaseTextPreprocessingResult

from core.basic_models.requirement.basic_requirements import Requirement
from scenarios.user.user_model import User


class SettingsRequirement(Requirement):
    def __init__(self, items: dict[str, Any], id: str | None = None) -> None:
        super().__init__(items, id)
        self._config = items.get("config", "template_settings")
        self._key = items["key"]
        self._value = items["value"]

    def _check(self, text_preprocessing_result: BaseTextPreprocessingResult, user: User,
               params: dict[str, Any] = None) -> bool:
        return user.settings[self._config][self._key] == self._value

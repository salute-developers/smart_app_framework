from typing import Dict, Any, Optional

from core.basic_models.requirement.constants import INSTANCE_CACHE_LEVEL
from core.text_preprocessing.base import BaseTextPreprocessingResult

from core.basic_models.requirement.basic_requirements import Requirement
from scenarios.user.user_model import User


class SettingsRequirement(Requirement):
    cache_level = INSTANCE_CACHE_LEVEL

    def __init__(self, items: Dict[str, Any], id: Optional[str] = None) -> None:
        super().__init__(items, id)
        self._config = items.get("config", "template_settings")
        self._key = items["key"]
        self._value = items["value"]

    def check(self, text_preprocessing_result: BaseTextPreprocessingResult, user: User,
              params: Dict[str, Any] = None) -> bool:
        return user.settings[self._config][self._key] == self._value

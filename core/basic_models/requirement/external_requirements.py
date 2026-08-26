from __future__ import annotations

from typing import Any

from core.basic_models.requirement.basic_requirements import Requirement, requirement_factory
from core.model.base_user import BaseUser

from core.text_preprocessing.base import BaseTextPreprocessingResult

from core.descriptions.smart_updatable_descriptions_items import SmartUpdatableDescriptionsItems


class ExternalRequirements(SmartUpdatableDescriptionsItems):
    def __init__(self, items):
        super().__init__(requirement_factory, items, ordered=True)


class ExternalRequirement(Requirement):
    requirement: str

    def __init__(self, items: dict[str, Any], id: str | None = None) -> None:
        super().__init__(items, id)
        self.requirement = items["requirement"]

    def check(self, text_preprocessing_result: BaseTextPreprocessingResult, user: BaseUser,
              params: dict[str, Any] = None) -> bool:
        requirement = user.descriptions["external_requirements"][self.requirement]
        return requirement.check(text_preprocessing_result, user, params)

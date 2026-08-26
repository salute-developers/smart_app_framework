from __future__ import annotations

from typing import Any

from core.basic_models.requirement.basic_requirements import Requirement
from core.model.factory import factory, list_factory
from core.text_preprocessing.base import BaseTextPreprocessingResult
from core.utils.exception_handlers import exc_handler
from scenarios.scenario_models.field.field_filler_description import FieldFillerDescription
from scenarios.user.user_model import User


class RequirementFiller(FieldFillerDescription):
    requirement: Requirement
    internal_item: FieldFillerDescription

    FIELD_KEY = "filler"

    def __init__(self, items: dict[str, Any], id: str | None = None):
        super().__init__(items, id)
        self._requirement: str = items["requirement"]
        # can be used not only with filters but with every entity which implements FieldFillerDescription interface
        # to not change statics "item" key is added
        self._item: str = items[self.FIELD_KEY]

        self.requirement = self.build_requirement()
        self.internal_item = self.build_internal_item()

    @factory(Requirement)
    def build_requirement(self) -> str:
        return self._requirement

    @factory(FieldFillerDescription)
    def build_internal_item(self) -> str:
        return self._item

    @exc_handler(on_error_obj_method_name="on_extract_error")
    def extract(self, text_preprocessing_result: BaseTextPreprocessingResult,
                user: User, params: dict[str, Any] = None) -> int | float | str | bool | list | dict | None:
        if self.requirement.check(text_preprocessing_result, user, params):
            return self.internal_item.run(user, text_preprocessing_result, params)


class ChoiceFiller(FieldFillerDescription):
    items: list[RequirementFiller]
    else_item: FieldFillerDescription | None

    FIELD_REQUIREMENT_KEY = "requirement_fillers"
    FIELD_ELSE_KEY = "else_filler"

    def __init__(self, items: dict[str, Any], id: str | None = None):
        super().__init__(items, id)
        self._requirement_items: list[str] = items[self.FIELD_REQUIREMENT_KEY]
        self._else_item: str | None = items.get(self.FIELD_ELSE_KEY)

        self.items = self.build_items()

        if self._else_item:
            self.else_item = self.build_else_item()
        else:
            self.else_item = None

    @list_factory(RequirementFiller)
    def build_items(self) -> list[str]:
        return self._requirement_items

    @factory(FieldFillerDescription)
    def build_else_item(self) -> str | None:
        return self._else_item

    @exc_handler(on_error_obj_method_name="on_extract_error")
    def extract(self, text_preprocessing_result: BaseTextPreprocessingResult,
                user: User, params: dict[str, Any] = None) -> int | float | str | bool | list | dict | None:
        for item in self.items:
            if item.requirement.check(text_preprocessing_result, user, params):
                return item.internal_item.run(user, text_preprocessing_result, params)
        if self._else_item:
            return self.else_item.run(user, text_preprocessing_result, params)


class ElseFiller(FieldFillerDescription):
    requirement: Requirement
    item: RequirementFiller
    else_item: FieldFillerDescription | None

    FIELD_ITEM_KEY = "filler"
    FIELD_ELSE_KEY = "else_filler"

    def __init__(self, items: dict[str, Any], id: str | None = None):
        super().__init__(items, id)
        self._requirement: str = items["requirement"]
        self._item: str = items[self.FIELD_ITEM_KEY]
        self._else_item: str | None = items.get(self.FIELD_ELSE_KEY)

        self.requirement = self.build_requirement()
        self.item = self.build_item()
        if self._else_item:
            self.else_item = self.build_else_item()
        else:
            self.else_item = None

    @factory(Requirement)
    def build_requirement(self) -> str:
        return self._requirement

    @factory(FieldFillerDescription)
    def build_item(self) -> str:
        return self._item

    @factory(FieldFillerDescription)
    def build_else_item(self) -> str | None:
        return self._else_item

    @exc_handler(on_error_obj_method_name="on_extract_error")
    def extract(self, text_preprocessing_result: BaseTextPreprocessingResult,
                user: User, params: dict[str, Any] = None) -> int | float | str | bool | list | dict | None:
        if self.requirement.check(text_preprocessing_result, user, params):
            return self.item.run(user, text_preprocessing_result, params)
        elif self._else_item:
            return self.else_item.run(user, text_preprocessing_result, params)

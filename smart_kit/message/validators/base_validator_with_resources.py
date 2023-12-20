from __future__ import annotations

from abc import ABC
from typing import Optional

from core.message.validators.base_validator import BaseMessageValidator, OnException
from smart_kit.resources import SmartAppResources


class BaseMessageValidatorWithResources(BaseMessageValidator, ABC):
    def __init__(self, resources: Optional[SmartAppResources] = None, on_exception: OnException = "raise",
                 *args, **kwargs):
        super().__init__(on_exception)
        self._resources: Optional[SmartAppResources] = None
        self.resources = resources

    @property
    def resources(self):
        return self._resources

    @resources.setter
    def resources(self, value: SmartAppResources):
        self._resources = value
        if self._resources is not None:
            self._update_resources()

    def _update_resources(self):
        pass

from functools import cached_property
from typing import TypeVar, Dict, Any

from core.basic_models.parametrizers.filter import Filter

T = TypeVar("T")


class BasicParametrizer:
    def __init__(self, user, items):
        self._user = user
        self._filter = items.get("filter") or {}

    @cached_property
    def filter(self):
        return Filter(self._filter)

    def filter_out(self, data: T, filter_params=None) -> T:
        return self.filter.filter_out(data, self._user, filter_params)

    def _get_user_data(self, text_preprocessing_result=None) -> Dict[str, Any]:
        return {"message": self._user.message}

    def collect(self, text_preprocessing_result=None, filter_params=None) -> Dict[str, Any]:
        data = self._get_user_data(text_preprocessing_result)
        return self.filter_out(data, filter_params)

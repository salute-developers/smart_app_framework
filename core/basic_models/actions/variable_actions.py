import collections
import json
from typing import Optional, Dict, Any, Union, List

from jinja2 import exceptions as jexcept

from core.basic_models.actions.basic_actions import Action
from core.basic_models.actions.command import Command
from core.basic_models.parametrizers.parametrizer import BasicParametrizer
from core.model.base_user import BaseUser
from core.text_preprocessing.base import BaseTextPreprocessingResult
from core.unified_template.unified_template import UnifiedTemplate


class BaseSetVariableAction(Action):
    key: str
    loader: Optional[str]
    loaders = collections.defaultdict(str, {"json": json.loads, "float": float, "int": int})
    value: Union[str, Dict]

    def __init__(self, items: Dict[str, Any], id: Optional[str] = None):
        super().__init__(items, id)
        self.key: str = items["key"]
        self.loader = items.get('loader')
        value: str = items["value"]
        self.template: UnifiedTemplate = UnifiedTemplate(value)

    def _set(self, user, value):
        raise NotImplementedError

    def run(self, user: BaseUser, text_preprocessing_result: BaseTextPreprocessingResult,
            params: Optional[Dict[str, Union[str, float, int]]] = None) -> List[Command]:
        commands = []
        params = user.parametrizer.collect(text_preprocessing_result)
        try:
            # if path is wrong, it may fail with UndefinedError
            # notion: {key: None} will return "None";
            # not existing key or value "" will return ""; otherwise question in scenario will go in cycles
            value = self.template.render(params)
        except jexcept.UndefinedError:
            value = None

        if self.loader:
            if value:
                loader = self.loaders[self.loader]
                value = loader(value)
            else:
                value = None

        self._set(user, value)
        return commands


class SetVariableAction(BaseSetVariableAction):
    version: Optional[int]
    parametrizer: BasicParametrizer
    loader: Optional[str]
    key: str
    loaders = collections.defaultdict(str, {"json": json.loads, "float": float, "int": int})
    ttl: int
    value: Union[str, Dict]

    def __init__(self, items: Dict[str, Any], id: Optional[str] = None):
        super().__init__(items, id)
        self.ttl: int = items.get("ttl")

    def _set(self, user, value):
        user.variables.set(self.key, value, self.ttl)


class DeleteVariableAction(Action):
    version: Optional[int]
    key: str

    def __init__(self, items: Dict[str, Any], id: Optional[str] = None):
        super().__init__(items, id)
        self.key: str = items["key"]

    def run(self, user: BaseUser, text_preprocessing_result: BaseTextPreprocessingResult,
            params: Optional[Dict[str, Union[str, float, int]]] = None) -> List[Command]:
        commands = []
        user.variables.delete(self.key)
        return commands


class ClearVariablesAction(Action):
    version: Optional[int]

    def __init__(self, items: Dict[str, Any] = None, id: Optional[str] = None):
        super().__init__(items, id)

    def run(self, user: BaseUser, text_preprocessing_result: BaseTextPreprocessingResult,
            params: Optional[Dict[str, Union[str, float, int]]] = None) -> List[Command]:
        commands = []
        user.variables.clear()
        return commands


class SetLocalVariableAction(BaseSetVariableAction):
    def _set(self, user, value):
        user.local_vars.set(self.key, value)

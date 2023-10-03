# coding: utf-8
import asyncio
import random
from typing import Union, Dict, List, Any, Optional

import core.logging.logger_constants as log_const
from core.basic_models.actions.command import Command
from core.basic_models.requirement.basic_requirements import Requirement
from core.configs.global_constants import KAFKA
from core.logging.logger_utils import log
from core.model.base_user import BaseUser
from core.model.factory import build_factory, factory, list_factory
from core.model.registered import Registered
from core.text_preprocessing.base import BaseTextPreprocessingResult

actions = Registered()
action_factory = build_factory(actions)


class Action:
    """ Базовый класс для действий в сценариях, хранящий информацию о сценарии: id, version.

    Запуск действия обеспечивается методом run. В случае ошибки выполнения вызывается метод on_run_error. Атрибут id
    используется в качестве идентификатора действия, по которому можно вызвать действие. Атрибут version используется
    для отслеживания версии объекта, например, при обновлении SmartUpdatableDescriptionsItems.
    """
    version: Optional[int]
    id: Optional[str]

    def __init__(self, items: Optional[Dict[str, Any]] = None, id: Optional[str] = None):
        items = items or {}
        self.id = id
        self.version = items.get("version", -1)

    async def run(self, user: BaseUser, text_preprocessing_result: BaseTextPreprocessingResult,
                  params: Optional[Dict[str, Union[str, float, int]]] = None) -> Optional[List[Command]]:
        raise NotImplementedError

    def on_run_error(self, text_preprocessing_result: BaseTextPreprocessingResult, user: BaseUser):
        log("exc_handler: Action failed to run. Return None. MESSAGE: %(masked_message)s.", user,
            {log_const.KEY_NAME: log_const.HANDLED_EXCEPTION_VALUE,
             "masked_message": user.message.masked_value},
            level="ERROR", exc_info=True)
        return None


class CommandAction(Action):
    """ Базовый класс для запроса к другому сервису, хранящий информацию о типе, методе и данных запроса.

    """
    DEFAULT_REQUEST_TYPE = KAFKA
    version: Optional[int]
    command: str
    request_type: Optional[str]
    request_data: Optional[Dict[str, str]]

    def __init__(self, items: Dict[str, Any], id: Optional[str] = None):
        super().__init__(items, id)
        items = items or {}
        self.command = items.get("command")
        self.request_type = items.get("request_type") or self.DEFAULT_REQUEST_TYPE
        self.request_data = items.get("request_data")


class DoingNothingAction(CommandAction):
    version: Optional[int]
    command: str
    nodes: Dict[str, str]

    def __init__(self, items: Dict[str, Any], id: Optional[str] = None):
        super().__init__(items, id)
        self.nodes = items.get("nodes") or {}

    async def run(self, user: BaseUser, text_preprocessing_result: BaseTextPreprocessingResult,
                  params: Optional[Dict[str, Union[str, float, int]]] = None) -> List[Command]:
        commands = []
        commands.append(Command(self.command, self.nodes, self.id, request_type=self.request_type,
                                request_data=self.request_data))
        return commands


class RequirementAction(Action):
    version: Optional[int]
    requirement: Requirement
    internal_item: Action

    FIELD_KEY = "action"

    def __init__(self, items: Dict[str, Any], id: Optional[str] = None):
        super().__init__(items, id)
        self._requirement: str = items["requirement"]
        # can be used not only with actions but with every entity which implements Action interface
        # to not change statics "item" key is added
        self._item: str = items[self.FIELD_KEY]

        self.requirement = self.build_requirement()
        self.internal_item = self.build_internal_item()

    @factory(Requirement)
    def build_requirement(self) -> str:
        return self._requirement

    @factory(Action)
    def build_internal_item(self) -> str:
        return self._item

    async def run(self, user: BaseUser, text_preprocessing_result: BaseTextPreprocessingResult,
                  params: Optional[Dict[str, Union[str, float, int]]] = None) -> List[Command]:
        commands = []
        if self.requirement.check(text_preprocessing_result, user, params):
            commands.extend(await self.internal_item.run(user, text_preprocessing_result, params) or [])
        return commands


class ChoiceAction(Action):
    version: Optional[int]
    items: List[RequirementAction]
    else_item: Optional[Action]

    FIELD_REQUIREMENT_KEY = "requirement_actions"
    FIELD_ELSE_KEY = "else_action"

    def __init__(self, items: Dict[str, Any], id: Optional[str] = None):
        super().__init__(items, id)
        self._requirement_items: List[str] = items[self.FIELD_REQUIREMENT_KEY]
        self._else_item: Optional[str] = items.get(self.FIELD_ELSE_KEY)

        self.items = self.build_items()

        if self._else_item:
            self.else_item = self.build_else_item()
        else:
            self.else_item = None

    @list_factory(RequirementAction)
    def build_items(self) -> List[str]:
        return self._requirement_items

    @factory(Action)
    def build_else_item(self) -> Optional[str]:
        return self._else_item

    async def run(self, user: BaseUser, text_preprocessing_result: BaseTextPreprocessingResult,
                  params: Optional[Dict[str, Union[str, float, int]]] = None) -> List[Command]:
        commands = []
        choice_is_made = False
        for item in self.items:
            checked = item.requirement.check(text_preprocessing_result, user, params)
            if checked:
                commands.extend(await item.internal_item.run(user, text_preprocessing_result, params) or [])
                choice_is_made = True
                break
        if not choice_is_made and self._else_item:
            commands.extend(await self.else_item.run(user, text_preprocessing_result, params) or [])
        return commands


class ElseAction(Action):
    version: Optional[int]
    requirement: Requirement
    item: Action
    else_item: Optional[Action]

    FIELD_ITEM_KEY = "action"
    FIELD_ELSE_KEY = "else_action"

    def __init__(self, items: Dict[str, Any], id: Optional[str] = None):
        super().__init__(items, id)
        self._requirement: str = items["requirement"]
        self._item: str = items[self.FIELD_ITEM_KEY]
        self._else_item: Optional[str] = items.get(self.FIELD_ELSE_KEY)

        self.requirement = self.build_requirement()
        self.item = self.build_item()
        if self._else_item:
            self.else_item = self.build_else_item()
        else:
            self.else_item = None

    @factory(Requirement)
    def build_requirement(self) -> str:
        return self._requirement

    @factory(Action)
    def build_item(self) -> str:
        return self._item

    @factory(Action)
    def build_else_item(self) -> Optional[str]:
        return self._else_item

    async def run(self, user: BaseUser, text_preprocessing_result: BaseTextPreprocessingResult,
                  params: Optional[Optional[Dict[str, Union[str, float, int]]]] = None) -> List[Command]:
        commands = []
        if self.requirement.check(text_preprocessing_result, user, params):
            commands.extend(await self.item.run(user, text_preprocessing_result, params) or [])
        elif self._else_item:
            commands.extend(await self.else_item.run(user, text_preprocessing_result, params) or [])
        return commands


class ActionOfActions(Action):
    version: Optional[int]
    actions: List[Action]

    def __init__(self, items: Dict[str, Any], id: Optional[str] = None):
        super().__init__(items, id)
        self._actions: List[str] = items.get("actions") or []
        self.actions = self.build_actions()

    @list_factory(Action)
    def build_actions(self) -> List[Action]:
        return self._actions


class CompositeAction(ActionOfActions):
    async def run(self, user: BaseUser, text_preprocessing_result: BaseTextPreprocessingResult,
                  params: Optional[Dict[str, Union[str, float, int]]] = None) -> List[Command]:
        commands = []
        for action in self.actions:
            commands.extend(await action.run(user, text_preprocessing_result, params) or [])
        return commands


class NonRepeatingAction(ActionOfActions):
    last_action_ids_storage: str

    def __init__(self, items: Dict[str, Any], id: Optional[str] = None):
        super().__init__(items, id)
        self._actions_count = len(items["actions"])
        self._last_action_ids_storage = items["last_action_ids_storage"]

    async def run(self, user: BaseUser, text_preprocessing_result: BaseTextPreprocessingResult,
                  params: Optional[Dict[str, Union[str, float, int]]] = None) -> List[Command]:
        commands = []
        last_ids = user.last_action_ids[self._last_action_ids_storage]
        all_indexes = list(range(self._actions_count))
        max_last_ids_count = self._actions_count - 1
        # get last_actions_ids slice with max_len of max_last_ids_count
        last_actions_ids = last_ids.get_list()[-max_last_ids_count:]
        available_indexes = list(set(all_indexes) - set(last_actions_ids))
        action_index = random.choice(available_indexes)
        action = self.actions[action_index]
        last_ids.add(action_index)
        commands.extend(await action.run(user, text_preprocessing_result, params) or [])
        return commands


class RandomAction(Action):
    actions: List[Action]

    def __init__(self, items: Dict[str, Any], id: Optional[str] = None):
        super().__init__(items, id)
        self._raw_actions: List[str] = items["actions"]
        self.actions = self.build_actions()

    @list_factory(Action)
    def build_actions(self) -> List[Action]:
        return self._raw_actions

    async def run(self, user: BaseUser, text_preprocessing_result: BaseTextPreprocessingResult,
                  params: Optional[Dict[str, Union[str, float, int]]] = None) -> List[Command]:
        commands = []
        pos = random.randint(0, len(self._raw_actions) - 1)
        action = self.actions[pos]
        commands.extend(await action.run(user, text_preprocessing_result, params=params) or [])
        return commands

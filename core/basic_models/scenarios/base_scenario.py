# coding: utf-8
from typing import Dict, Any, List

import core.logging.logger_constants as log_const
import scenarios.logging.logger_constants as scenarios_log_const
from core.basic_models.actions.basic_actions import Action
from core.basic_models.actions.command import Command
from core.basic_models.requirement.basic_requirements import Requirement
from core.logging.logger_utils import log
from core.model.base_user import BaseUser
from core.model.factory import build_factory, list_factory
from core.model.factory import factory
from core.model.registered import Registered
from core.text_preprocessing.base import BaseTextPreprocessingResult

scenarios = Registered()

scenario_factory = build_factory(scenarios)


class BaseScenario:
    EMPTY_ANSWER_KEY = "default_empty_answer"

    scenario_description: str
    switched_off: bool
    version: int
    empty_answer: Action
    actions: List[Action]
    available_requirement: Requirement

    def __init__(self, items, id):
        self._actions = items.get("actions")
        self._available_requirement = items.get("availabe_requirement")
        self._default_empty_answer = {"type": "external", "action": self.EMPTY_ANSWER_KEY}
        self._empty_answer = items.get("empty_answer", self._default_empty_answer)
        self.id = id
        self.root_id = items.get("root_id", self.id)
        self.scenario_description = items.get("scenario_description", "")
        self.switched_off = items.get("switched_off", False)
        self.version = items.get("version", -1)

        self.empty_answer = self.build_empty_answer()
        self.actions = self.build_actions()
        self.available_requirement = self.build_available_requirement()

    @factory(Action)
    def build_empty_answer(self):
        return self._empty_answer

    @list_factory(Action)
    def build_actions(self):
        return self._actions

    @factory(Requirement)
    def build_available_requirement(self):
        return self._available_requirement

    def check_available(self, text_preprocessing_result: BaseTextPreprocessingResult, user: BaseUser) -> bool:
        if not self.switched_off:
            return self.available_requirement.check(text_preprocessing_result, user)
        return False

    def _log_params(self) -> Dict[str, str]:
        return {log_const.KEY_NAME: log_const.SCENARIO_VALUE}

    def text_fits(self, text_preprocessing_result, user):
        return False

    async def get_no_commands_action(self, user, text_preprocessing_result,
                                     params: Dict[str, Any] = None) -> List[Command]:
        log_params = {log_const.KEY_NAME: scenarios_log_const.CHOSEN_ACTION_VALUE,
                      scenarios_log_const.CHOSEN_ACTION_VALUE: self._empty_answer}
        log(scenarios_log_const.CHOSEN_ACTION_MESSAGE, user, log_params)
        try:
            empty_answer = await self.empty_answer.run(user, text_preprocessing_result, params) or []
        except KeyError:
            log_params = {log_const.KEY_NAME: scenarios_log_const.CHOSEN_ACTION_VALUE}
            log("Scenario has empty answer, but empty_answer action isn't defined",
                params=log_params, level='WARNING')
            empty_answer = []
        return empty_answer

    async def get_action_results(self, user, text_preprocessing_result,
                                 actions: List[Action], params: Dict[str, Any] = None) -> List[Command]:
        results = []
        for action in actions:
            result = await action.run(user, text_preprocessing_result, params) or []
            log_params = self._log_params()
            log_params["class"] = action.__class__.__name__
            log("called action: %(class)s", user, log_params)

            if result:
                for command in result:
                    if command.action_id:
                        log_params = self._log_params()
                        log_params["id"] = command.action_id
                        log("external action id: %(id)s", user, log_params)

                    log_params = self._log_params()
                    log_params["name"] = command.name
                    log("action result name: %(name)s", user, log_params)
                results.extend(result)
        return results

    @property
    def history(self):
        return {"scenario_path": [{"scenario": self.id, "node": None}]}

    async def run(self, text_preprocessing_result, user, params: Dict[str, Any] = None) -> List[Command]:
        return await self.get_action_results(user, text_preprocessing_result, self.actions, params)

# coding: utf-8
from functools import cached_property

from core.basic_models.actions.basic_actions import Action
from core.basic_models.requirement.basic_requirements import Requirement
from core.model.factory import factory, list_factory


class TreeScenarioNode:
    def __init__(self, items, id):
        items = items or {}
        self.id = id
        self.form_key = items["form_key"]
        self._requirement = items.get("requirement")
        self._actions = items.get("actions")
        self.available_nodes = items.get("available_nodes")

    @cached_property
    @factory(Requirement)
    def requirement(self):
        return self._requirement

    @cached_property
    @list_factory(Action)
    def actions(self):
        return self._actions

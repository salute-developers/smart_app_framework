# coding: utf-8
import time
from functools import cached_property

from core.basic_models.actions.basic_actions import Action
from core.model.factory import factory


class BehaviorDescription:
    def __init__(self, items, id=None):
        self.id = id
        self._success_action = items["success_action"]
        self._fail_action = items.get("fail_action")
        self._misstate = items.get("misstate")
        self._timeout_action = items.get("timeout_action")
        self._timeout = items.get("timeout", 300)
        self.version = items.get("version", -1)
        self.loop_def = items.get("loop_def", True)

    def get_expire_time_from_now(self, user):
        return time.time() + self.timeout(user)

    def timeout(self, user):
        setting_timeout = user.settings["template_settings"].get("services_timeout", {}).get(self.id)
        return setting_timeout or self._timeout

    @cached_property
    @factory(Action)
    def success_action(self):
        return self._success_action

    @cached_property
    @factory(Action)
    def fail_action(self):
        return self._fail_action

    @cached_property
    @factory(Action)
    def misstate(self):
        return self._misstate

    @cached_property
    @factory(Action)
    def timeout_action(self):
        return self._timeout_action

# coding: utf-8
import json
from functools import cached_property
from typing import List

from core.descriptions.descriptions import Descriptions
from core.model.queued_objects.limited_queued_hashable_objects_description import \
    LimitedQueuedHashableObjectsDescription
from core.model.queued_objects.limited_queued_hashable_objects import LimitedQueuedHashableObjects, \
    LimitedQueuedHashableObjectsItems
from core.logging.logger_utils import log
from core.model.field import Field
from core.model.model import Model
from core.basic_models.parametrizers.parametrizer import BasicParametrizer
from core.basic_models.counter.counters import Counters
from core.basic_models.variables.variables import Variables
from scenarios.logging.logger_constants import KEY_NAME


class BaseUser(Model):
    USER_DB_VERSION = "user_db_data_version"

    counters: Counters
    variables: Variables
    private_vars: Variables
    local_vars: Variables
    descriptions: Descriptions

    def __init__(self, id, message, values, descriptions, load_error=False):
        self.id = id
        self.message = message
        self.descriptions = descriptions
        self.load_error = load_error
        super().__init__(values=values, user=self)
        self._initialize()

    def _initialize(self):
        """Add here some things to do after creating fields."""
        pass

    @cached_property
    def parametrizer(self):
        return BasicParametrizer(self, {})

    @property
    def fields(self) -> List[Field]:
        return [
            Field("counters", Counters),
            Field("last_action_ids", LimitedQueuedHashableObjectsItems, self.descriptions["last_action_ids"]),
            Field("last_messages_ids", LimitedQueuedHashableObjects, LimitedQueuedHashableObjectsDescription(None)),
            Field("local_vars", Variables, None, False),
            Field("variables", Variables),
            Field("private_vars", Variables),
        ]

    @property
    def raw_str(self):
        # Attention: non-serializable objects will become str with error message
        raw = json.dumps(self.raw, default=lambda o: f"<non-serializable: {type(o).__qualname__}>")
        log("%(class_name)s.raw USER %(uid)s SAVE db_version = %(db_version)s. "
            "Saving User %(uid)s. Serialized utf8 json length is %(user_length)s symbols.", self,
            {"db_version": str(self.private_vars.get(self.USER_DB_VERSION)),
             "uid": str(self.id), "user_length": len(raw),
             KEY_NAME: "user_save"})
        return raw

    def expire(self):
        self.counters.expire()
        self.variables.expire()
        self.private_vars.expire()
        self.local_vars.expire()

from functools import cached_property

from core.model.factory import dict_factory, factory
from scenarios.scenario_models.field.field_filler_description import FieldFillerDescription
from scenarios.scenario_models.field.field_descriptions.basic_field_description import BasicFieldDescription


class CompositeFieldDescription(BasicFieldDescription):

    def __init__(self, items, id):
        super(CompositeFieldDescription, self).__init__(items, id)
        self._fields = items["fields"]

    @cached_property
    @factory(FieldFillerDescription)
    def filler(self):
        return self._filler

    @cached_property
    @dict_factory(BasicFieldDescription)
    def fields(self):
        return self._fields

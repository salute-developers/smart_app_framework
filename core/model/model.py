# coding: utf-8
from typing import Dict, Any


class Model:
    __slots__ = ['_fields']
    @property
    def fields(self):
        return []

    def __init__(self, values, user):
        self._fields = []
        values = values or {}

        for field in self.fields:
            value = values.get(field.name)
            description = field.description
            args = field.args
            if description is not None:
                obj = field.model(value, description, user, *args)
            else:
                obj = field.model(value, user, *args)
            self._fields[field.name] = obj

    def get_field(self, name):
        return getattr(self, name)

    @property
    def raw(self) -> Dict[str, Any]:
        result = {}
        for field in self.fields:
            value = getattr(self, field.name)
            raw = value.raw
            if raw is not None:
                result[field.name] = raw
        return result

    def __getattr__(self, item):
        return self._fields[item]

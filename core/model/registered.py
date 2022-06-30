# coding: utf-8
from typing import TypeVar, Union

T = TypeVar("T")


class Registered(dict):

    def __getitem__(self, key: Union[str, T]) -> T:
        value = self.get(key, key)
        assert not isinstance(value, str), "{} factory is not registered".format(key)
        return value


registered_factories = Registered()

from __future__ import annotations

from typing import TypeVar, Union

T = TypeVar("T")


class Registered(dict):

    def __getitem__(self, key: str | T) -> T:
        value = self.get(key, key)
        assert not isinstance(value, str), f"{key} factory is not registered"
        return value


registered_factories = Registered()

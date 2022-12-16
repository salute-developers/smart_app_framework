from typing import TypeVar


T = TypeVar("T")


class Filter:
    def __init__(self, items):
        pass

    def filter_out(self, data: T, user, params=None) -> T:
        return data

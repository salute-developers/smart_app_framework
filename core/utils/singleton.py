from __future__ import annotations
from typing import TypeVar

T = TypeVar("T")


class Singleton(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super().__call__(*args, **kwargs)
        return cls._instances[cls]

    def get_instance(cls: type[T]) -> T | None:
        return cls._instances.get(cls)


class SingletonOneInstance(type):
    _instance = None

    def __call__(cls, *args, **kwargs):
        if SingletonOneInstance._instance is None:
            SingletonOneInstance._instance = super().__call__(*args, **kwargs)
        return SingletonOneInstance._instance

    def get_instance(cls: type[T]) -> T | None:
        return SingletonOneInstance._instance

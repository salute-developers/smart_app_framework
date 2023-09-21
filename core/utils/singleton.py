from __future__ import annotations
from typing import TypeVar, Optional, Type

T = TypeVar("T")


class Singleton(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]

    def get_instance(cls: Type[T]) -> Optional[T]:
        return cls._instances.get(cls)


class SingletonOneInstance(type):
    _instance = None

    def __call__(cls, *args, **kwargs):
        if SingletonOneInstance._instance is None:
            SingletonOneInstance._instance = super(SingletonOneInstance, cls).__call__(*args, **kwargs)
        return SingletonOneInstance._instance

    def get_instance(cls: Type[T]) -> Optional[T]:
        return SingletonOneInstance._instance

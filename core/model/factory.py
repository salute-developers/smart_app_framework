# coding: utf-8
import functools
from collections import OrderedDict
from typing import TypeVar, Type, List, Callable, Any, Dict

from core.model.registered import registered_factories, Registered

T = TypeVar("T")


def build_factory(registry_models: Registered) -> Callable:
    def _inner(items, *args, **kwargs):
        type = items.get("type")
        model = registry_models[type]
        try:
            return model(items, *args, **kwargs)
        except Exception:
            raise

    return _inner


def factory(type: Type[T], **params) -> Callable[[Type[T]], Callable]:
    def _inner(func: Callable) -> Callable:
        @functools.wraps(func)
        def _wrap(self, *args: Any, **kwargs: Any) -> T:
            result = func(self, *args, **kwargs)
            result = result or {}
            cls: Type[T] = registered_factories[type]
            if not isinstance(result, dict):
                result = cls(result)
            else:
                result = cls(result or {}, **params)
            return result

        return _wrap

    return _inner


def list_factory(type: Type[T], **params) -> Callable[[Type[T]], Callable]:
    def _inner(func: Callable) -> Callable:
        @functools.wraps(func)
        def _wrap(*args: Any, **kwargs: Any) -> List[T]:
            cls: Type[T] = registered_factories[type]
            res: List[T] = []
            for items in func(*args, **kwargs) or []:
                if not isinstance(items, dict):
                    res.append(cls(items))
                else:
                    res.append(cls(items or {}, **params))
            return res

        return _wrap

    return _inner


def dict_factory(type: Type[T], has_id=True) -> Callable[[Type[T]], Callable]:
    def _inner(func: Callable) -> Callable:
        @functools.wraps(func)
        def _wrap(*args: Any, **kwargs: Any) -> Dict[str, T]:
            cls: Type[T] = registered_factories[type]
            items_iterator = func(*args, **kwargs).items()
            if has_id:
                return {id: cls(id=id, items=items) for id, items in items_iterator or {}}
            else:
                return {id: cls(items) for id, items in items_iterator or {}}

        return _wrap

    return _inner


def ordered_dict_factory(type: Type[T], has_id=True) -> Callable[[Type[T]], Callable]:
    def _inner(func: Callable) -> Callable:
        @functools.wraps(func)
        def _wrap(*args: Any, **kwargs: Any) -> 'OrderedDict[str, T]':
            cls: Type[T] = registered_factories[type]
            items_iterator = func(*args, **kwargs).items()
            result = OrderedDict({})
            for id, items in items_iterator:
                result[id] = cls(id=id, items=items) if has_id else cls(items)
            return result

        return _wrap

    return _inner

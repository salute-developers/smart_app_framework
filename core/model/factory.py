# coding: utf-8
import functools
from collections import OrderedDict
from typing import Type, List, Callable, Any, Dict

from core.model.registered import registered_factories, Registered


def build_factory(registry_models: Registered) -> Callable:
    def _inner(items, *args, **kwargs):
        _type = items.get("_type")
        model = registry_models[_type]
        try:
            return model(items, *args, **kwargs)
        except:
            raise

    return _inner


def factory(_type: Type, **params) -> Callable[[Type], Callable]:
    def _inner(func: Callable) -> Callable:
        @functools.wraps(func)
        def _wrap(self, *args: Any, **kwargs: Any) -> Any:
            result = func(self, *args, **kwargs)
            result = result or {}
            cls: Callable = registered_factories[_type]
            if not isinstance(result, dict):
                result = cls(result)
            else:
                result = cls(result or {}, **params)
            return result

        return _wrap

    return _inner


def list_factory(_type: Callable[[Any], Any], **params) -> Callable[[Type], Callable]:
    def _inner(func: Callable) -> Callable:
        @functools.wraps(func)
        def _wrap(*args: Any, **kwargs: Any) -> list:
            cls: Callable = registered_factories[_type]
            res: List = []
            for items in func(*args, **kwargs) or []:
                if not isinstance(items, dict):
                    res.append(cls(items))
                else:
                    res.append(cls(items or {}, **params))
            return res

        return _wrap

    return _inner


def dict_factory(_type: Callable[[Any], Any], has_id=True) -> Callable[[Type], Callable]:
    def _inner(func: Callable) -> Callable:
        @functools.wraps(func)
        def _wrap(*args: Any, **kwargs: Any) -> Dict[str, Any]:
            cls: Callable = registered_factories[_type]
            items_iterator = func(*args, **kwargs).items()
            if has_id:
                return {id: cls(id=id, items=items) for id, items in items_iterator or {}}
            else:
                return {id: cls(items) for id, items in items_iterator or {}}

        return _wrap

    return _inner


def ordered_dict_factory(_type: Callable[[Any], Any], has_id=True) -> Callable[[Type], Callable]:
    def _inner(func: Callable) -> Callable:
        @functools.wraps(func)
        def _wrap(*args: Any, **kwargs: Any) -> 'OrderedDict[str, Any]':
            cls: Callable = registered_factories[_type]
            items_iterator = func(*args, **kwargs).items()
            result = OrderedDict({})
            for id, items in items_iterator:
                result[id] = cls(id=id, items=items) if has_id else cls(items)
            return result

        return _wrap

    return _inner

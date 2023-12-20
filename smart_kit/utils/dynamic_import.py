from typing import Any
from importlib import import_module


def dynamic_import_object(x: str) -> Any:
    groups = x.split(".")
    module = import_module(".".join(groups[:-1]))
    return getattr(module, groups[-1])

from typing import Any
from collections.abc import Iterable

from core.model.factory import build_factory
from core.model.registered import Registered

comparators = Registered()

comparator_factory = build_factory(comparators)


class Comparator:
    def __init__(self, items: dict[str, Any] | None) -> None:
        pass

    def compare(self, left: Any, right: Any) -> bool:
        raise NotImplementedError


class MoreComparator(Comparator):
    def compare(self, left: int, right: int) -> bool:
        return left > right


class LessComparator(Comparator):
    def compare(self, left: int, right: int) -> bool:
        return left < right


class MoreOrEqualComparator(Comparator):
    def compare(self, left: int, right: int) -> bool:
        return left >= right


class LessOrEqualComparator(Comparator):
    def compare(self, left: int, right: int) -> bool:
        return left <= right


class EqualComparator(Comparator):
    def compare(self, left: int, right: int) -> bool:
        return left == right


class NotEqualComparator(Comparator):
    def compare(self, left: int, right: int) -> bool:
        return left != right


class InComparator(Comparator):
    def compare(self, left: Any, right: Iterable[Any]) -> bool:
        return left in right

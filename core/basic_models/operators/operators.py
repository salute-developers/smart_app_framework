from __future__ import annotations

from typing import Any

from core.basic_models.operators.comparators import MoreComparator, LessComparator, MoreOrEqualComparator, \
    LessOrEqualComparator, EqualComparator, NotEqualComparator, InComparator, Comparator
from core.model.factory import build_factory, list_factory
from core.model.registered import Registered

operators = Registered()

operator_factory = build_factory(operators)


class Operator:

    def __init__(self, items: dict[str, Any] | None) -> None:
        pass

    def compare(self, value: Any) -> bool:
        raise NotImplementedError


class CompositeOperator(Operator):
    operators: list[Operator]

    def __init__(self, items: dict[str, Any] | None) -> None:
        super().__init__(items)
        self._operators: dict[str, Any] = items["operators"]
        self.operators = self.build_operators()

    @list_factory(Operator)
    def build_operators(self):
        return self._operators

    def compare(self, value: Any) -> bool:
        return all(operator.compare(value) for operator in self.operators)


class AnyOperator(CompositeOperator):
    def compare(self, value: Any) -> bool:
        return any(operator.compare(value) for operator in self.operators)


class AmountOperator(Operator):
    amount: int | str | list
    comparator: Comparator

    def __init__(self, items: dict[str, Any] | None) -> None:
        super().__init__(items)
        self.amount = items["amount"]
        self.comparator: Comparator | None = None

    def compare(self, value: int | str):
        return self.comparator.compare(value, self.amount)


class InOperator(AmountOperator):
    amount: int | str | list
    comparator: InComparator

    def __init__(self, items: dict[str, Any] | None) -> None:
        super().__init__(items)
        self.comparator = InComparator({})


class MoreOperator(AmountOperator):
    amount: int | str | list
    comparator: MoreComparator

    def __init__(self, items: dict[str, Any] | None) -> None:
        super().__init__(items)
        self.comparator = MoreComparator({})


class LessOperator(AmountOperator):
    amount: int | str | list
    comparator: LessComparator

    def __init__(self, items: dict[str, Any] | None) -> None:
        super().__init__(items)
        self.comparator = LessComparator({})


class MoreOrEqualOperator(AmountOperator):
    amount: int | str | list
    comparator: MoreOrEqualComparator

    def __init__(self, items: dict[str, Any] | None) -> None:
        super().__init__(items)
        self.comparator = MoreOrEqualComparator({})


class LessOrEqualOperator(AmountOperator):
    amount: int | str | list
    comparator: LessOrEqualComparator

    def __init__(self, items: dict[str, Any] | None) -> None:
        super().__init__(items)
        self.comparator = LessOrEqualComparator({})


class EqualOperator(AmountOperator):
    amount: int | str | list
    comparator: EqualComparator

    def __init__(self, items: dict[str, Any] | None) -> None:
        super().__init__(items)
        self.comparator = EqualComparator({})


class NotEqualOperator(AmountOperator):
    amount: int | str | list
    comparator: NotEqualComparator

    def __init__(self, items: dict[str, Any] | None) -> None:
        super().__init__(items)
        self.comparator = NotEqualComparator({})


class Exists(Operator):
    def compare(self, value: Any) -> bool:
        return True if value is not None else False


class EndsWithOperator(AmountOperator):
    """
    Оператор проверяет, оканчивается ли значение на amount
    """

    def compare(self, value: int | str) -> bool:
        return str(value).endswith(str(self.amount)) if value else False


class StartsWithOperator(AmountOperator):
    """
    Оператор проверяет, начинается ли значение с amount
    """

    def compare(self, value: int | str) -> bool:
        return str(value).startswith(str(self.amount)) if value else False

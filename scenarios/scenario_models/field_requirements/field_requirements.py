from typing import Any

from core.basic_models.operators.operators import Operator
from core.model.factory import factory, build_factory, list_factory
from core.model.registered import Registered

field_requirements = Registered()

field_requirement_factory = build_factory(field_requirements)


class FieldRequirement:
    def __init__(self, items: dict[str, Any] | None) -> None:
        pass

    def check(self, field_value: str, params: dict[str, Any] = None) -> bool:
        return True


class CompositeFieldRequirement(FieldRequirement):
    requirements: list[FieldRequirement]

    def __init__(self, items: dict[str, Any] | None) -> None:
        super().__init__(items)
        self._requirements: list[dict[str, Any]] = items["requirements"]
        self.requirements = self.build_requirements()

    @list_factory(FieldRequirement)
    def build_requirements(self):
        return self._requirements


class AndFieldRequirement(CompositeFieldRequirement):
    def check(self, field_value: str, params: dict[str, Any] = None) -> bool:
        return all(requirement.check(field_value=field_value, params=params) for requirement in self.requirements)


class OrFieldRequirement(CompositeFieldRequirement):
    def check(self, field_value: str, params: dict[str, Any] = None) -> bool:
        return any(requirement.check(field_value=field_value, params=params) for requirement in self.requirements)


class NotFieldRequirement(FieldRequirement):
    requirement: FieldRequirement

    def __init__(self, items: dict[str, Any] | None) -> None:
        super().__init__(items)
        self._requirement: dict[str, Any] = items["requirement"]
        self.requirement = self.build_requirement()

    @factory(FieldRequirement)
    def build_requirement(self):
        return self._requirement

    def check(self, field_value: str, params: dict[str, Any] = None) -> bool:
        return not self.requirement.check(field_value=field_value, params=params)


class ComparisonFieldRequirement(FieldRequirement):
    operator: Operator

    def __init__(self, items: dict[str, Any] | None) -> None:
        super().__init__(items)
        self._operator: dict[str, Any] = items["operator"]
        self.operator = self.build_operator()

    @factory(Operator)
    def build_operator(self):
        return self._operator

    def check(self, field_value: str, params: dict[str, Any] = None) -> bool:
        return self.operator.compare(field_value)


class IsIntFieldRequirement(FieldRequirement):
    def __init__(self, items: dict[str, Any] | None) -> None:
        super().__init__(items)

    def check(self, field_value: str, params: dict[str, Any] = None) -> bool:
        try:
            int(field_value)
            return True
        except ValueError:
            return False


class ValueInSetRequirement(FieldRequirement):
    symbols: list

    def __init__(self, items: dict[str, Any] | None) -> None:
        super().__init__(items)
        self.symbols: set = set(items["symbols"])

    def check(self, field_value: str, params: dict[str, Any] = None) -> bool:
        return field_value in self.symbols


class TokenPartInSet(FieldRequirement):
    def __init__(self, items: dict[str, Any] | None) -> None:
        super().__init__(items)
        self.part = items['part']
        self.values = items['values']

    def check(self, field_value: dict, params: dict[str, Any] = None) -> bool:
        return field_value[self.part] in self.values


class TextLengthFieldRequirement(FieldRequirement):
    min_field_length: int
    max_field_length: int

    def __init__(self, items: dict[str, Any] | None) -> None:
        super().__init__(items)
        self.min_field_length = items["min_field_length"]
        self.max_field_length = items["max_field_length"]

    def check(self, field_value: str, params: dict[str, Any] = None) -> bool:
        return self.min_field_length <= len(field_value) <= self.max_field_length

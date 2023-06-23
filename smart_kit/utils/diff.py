from __future__ import annotations

import json
import re
from functools import singledispatchmethod
from typing import Dict, Any, Tuple

import tabulate

DoesNotExpected = object()


class Diff:
    def __init__(self):
        self.missed: Dict[str, Any] = {}  # key : expected
        self.different: Dict[str, Tuple[Any, Any]] = {}  # key: expected,actual
        self.does_not_expected: Dict[str, Any] = {}  # key: actual

    @singledispatchmethod
    @classmethod
    def partial_diff(cls, expected: Any, actual: Any, path="", dict_check_does_not_expected=False) -> Diff:
        diff = cls()
        if expected != actual and \
                not (isinstance(actual, str) and isinstance(expected, str) and re.fullmatch(expected, actual)):
            diff.different[path] = expected, actual
        return diff

    @partial_diff.register(list)
    @classmethod
    def partial_diff_list(cls, expected: list, actual: list, path="", dict_check_does_not_expected=False) -> Diff:
        diff = cls()

        if not isinstance(actual, list):
            diff.different[path] = expected, actual
            return diff

        does_not_expected = [DoesNotExpected for _ in range(len(expected), len(actual))]

        for index, exp_element in enumerate(expected + does_not_expected):
            sub_path = f"{path}[{index + 1}]" if path else f"[{index + 1}]"
            try:
                if exp_element == DoesNotExpected:
                    diff.does_not_expected[sub_path] = actual[index]
                else:
                    diff.update(cls.partial_diff(exp_element, actual[index], sub_path, dict_check_does_not_expected))
            except IndexError:
                diff.missed[sub_path] = exp_element

        return diff

    @partial_diff.register(dict)
    @classmethod
    def partial_diff_dict(cls, expected: dict, actual: dict, path="", dict_check_does_not_expected=False) -> Diff:
        diff = cls()

        if not isinstance(actual, dict):
            diff.different[path] = expected, actual
            return diff

        if dict_check_does_not_expected:
            for key, value in actual.items():
                if key not in expected:
                    sub_path = f"{path}.{key}" if path else str(key)
                    diff.does_not_expected[sub_path] = value

        for key, value in expected.items():
            sub_path = f"{path}.{key}" if path else str(key)
            if key not in actual:
                diff.missed[sub_path] = value
                continue

            diff.update(cls.partial_diff(value, actual[key], sub_path, dict_check_does_not_expected))
        return diff

    def update(self, other: Diff):
        self.missed.update(other.missed)
        self.different.update(other.different)
        self.does_not_expected.update(other.does_not_expected)

    def __bool__(self):
        return bool(self.missed or self.different or self.does_not_expected)

    def __str__(self):
        ret = []
        if self.missed:
            missed = "Missed:\n" + tabulate.tabulate(self.missed.items(), headers=["Key", "Expected"])
            ret.append(missed)
        if self.does_not_expected:
            does_not_expected = "Does Not Expected:\n"
            does_not_expected += tabulate.tabulate(self.does_not_expected.items(), headers=["Key", "Actual"])
            ret.append(does_not_expected)
        if self.different:
            different = "Different:\n"
            different += tabulate.tabulate(
                [(k, d[0], d[1]) for k, d in self.different.items()], headers=["Key", "Expected", "Actual"]
            )
            ret.append(different)

        return "\n".join(ret)

    def __dict__(self):
        return {
            "missed": self.missed.copy(),
            "different": self.different.copy(),
            "does_not_expected": self.does_not_expected.copy(),
        }

    def serialize(self):
        return json.dumps(self.__dict__())

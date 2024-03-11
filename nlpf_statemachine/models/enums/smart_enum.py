"""
# SmartEnum.

SmartEnum - Enum, элемент которого эквивалентен строке.
"""
from enum import Enum
from typing import Any


class SmartEnum(str, Enum):
    """
    # Базовый класс для всех enum-ов.
    """

    def __eq__(self, other: Any) -> bool:
        """## Проверка эквивалентности."""
        return self.value == other

    def __hash__(self) -> int:
        """## Хэш."""
        return hash(self.value)

    def __str__(self) -> str:
        """## Строка, соответствующая выбранному элементу."""
        return str(self.value)

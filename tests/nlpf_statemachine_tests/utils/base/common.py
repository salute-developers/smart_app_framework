"""
# Общие утилиты.
"""
import random
import string
from typing import Any
from uuid import uuid4


def random_string(length: int = 10) -> str:
    """
    Генерация случайной строки определённой длины.

    Args:
        length (int): длина строки.

    Returns:
        str: сгенерированная строка.
    """
    return "".join(random.choices(string.ascii_letters + string.digits, k=length))


def random_guid() -> str:
    """
    Генерация случайной строки в формате guid.

    Returns:
        str: сгенерированная строка.
    """
    return str(uuid4())


class AnyObj:
    """
    # Мок для проверки любого объекта в ответе (MagicMock.assert_called_with).
    """

    def __eq__(self, other: Any) -> bool:
        """## Сравнение с другими объектами."""
        return True

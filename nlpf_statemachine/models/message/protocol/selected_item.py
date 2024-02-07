"""
# Результат работы ItemSelector.

Описание элемента экрана, который пользователь назвал при запросе
("включи второй" / "включи второго терминатора").
 Для работы этой функциональности нужна отправка во входящем сообщении с фронтенда item_selector со списком элементов.

Объект передается всегда и может быть либо пустым, либо содержать все указанные поля.
"""

from pydantic import BaseModel, Field


class SelectedItem(BaseModel):
    """
    # Описание модели SelectedItem.
    """

    index: int | None = Field(default=None)
    """Номер элемента из списка, начиная с 0."""
    title: str | None = Field(default=None)
    """Название элемента."""
    is_query_by_number: bool | None = Field(default=None)
    """Указывает выбор элемента по номеру."""

    def __bool__(self) -> bool:
        """Проверка наличия SelectedItem."""
        return self.index is not None

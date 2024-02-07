"""
# Модели для отладочной информации по работе ContextManager в транзакции в конкретном сценарии.

Данный объект можно использовать при написании тестов для проверки цепочки вызовов. Он возвращается в поле
`nlpf_statemachine.models.response.Response.debug_info`.
"""

from pydantic import BaseModel, Field


class CallHistoryItem(BaseModel):
    """Элемент истории вызовов экшенов."""

    event: str | None = Field(default=None)
    """Событие, которое отработало."""
    action: str
    """Экшен, который был вызван."""
    scenario: str
    """Сценарий, на котором был вызван action."""


class DebugInfo(BaseModel):
    """Коллекция отладочной информации по работе ContextManager в транзакции в конкретном сценарии."""

    base_event: str | None = Field(default=None)
    """Базовое событие текущей транзакции."""
    call_history: list[CallHistoryItem | None] = Field(default_factory=list)
    """Список вызовов."""
    transaction_finished: bool = Field(default=True)
    """Флаг на окончание транзакции."""
    static_code: str | None = Field(default=None)
    """Код ответа из статики."""

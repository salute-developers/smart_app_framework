"""
# Модели для отладочной информации по работе ContextManager в транзакции в конкретном сценарии.

Данный объект можно использовать при написании тестов для проверки цепочки вызовов. Он возвращается в поле
`nlpf_statemachine.models.response.Response.debug_info`.
"""
from typing import List, Optional

from pydantic import BaseModel, Field


class CallHistoryItem(BaseModel):
    """Элемент истории вызовов экшенов."""

    event: Optional[str] = Field(description="Событие, которое отработало.")
    """Событие, которое отработало."""

    action: str = Field(description="Экшен, который был вызван.")
    """Экшен, который был вызван."""

    scenario: str = Field(description="Сценарий, на котором был вызван action.")
    """Сценарий, на котором был вызван action."""


class DebugInfo(BaseModel):
    """Коллекция отладочной информации по работе ContextManager в транзакции в конкретном сценарии."""

    base_event: Optional[str] = Field(description="Базовое событие текущей транзакции.", default=None)
    """Базовое событие текущей транзакции."""

    call_history: List[CallHistoryItem] = Field(description="Список вызовов.", default_factory=list)
    """Список вызовов."""

    transaction_finished: bool = Field(description="Флаг на окончание транзакции.", default=True)
    """Флаг на окончание транзакции."""

    static_code: str = Field(description="Код ответа из статики.", default=None)
    """Код ответа из статики."""

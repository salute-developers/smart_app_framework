"""
# Переопределение контекста.

В рамках написания своего сценария можно переопределить как сам контекст, так и любой вложенный в него объект.
Но крайне не рекомендуется переопределять и изменять базовые поля модели Context.
"""
from typing import Optional

from pydantic import Field

from nlpf_statemachine.example.app.sc.models.token_service_integration import GetTokenResponseData
from nlpf_statemachine.models import Context, LocalContext


class ExampleLocalContext(LocalContext):
    """
    # Переопределение модели LocalContext.

    Модель LocalContext служит для описания полей контекста в рамках одной транзакции.
    Контекст создаётся при запуске транзакции и уничтожается при его завершении.
    """

    ihapi_token: Optional[GetTokenResponseData] = None
    """Токен ihapi."""
    retry_index: Optional[int] = None
    """Количество попыток загрузки данных из интеграции."""


class ExampleContext(Context):
    """
    # Переопределение модели Context.

    Модель Context служит для описания данных, которые сохраняются между запросами (=контекст).
    """

    local: ExampleLocalContext = Field(default_factory=ExampleLocalContext)
    """Контекст, живущий в рамках одной транзакции."""

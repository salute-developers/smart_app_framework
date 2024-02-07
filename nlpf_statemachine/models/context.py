"""
# Описание моделей контекста.

`Context` --- pydantic-модель для хранения данных между запросами. (хранится в объекте `User`)

`LocalContext` --- pydantic-модель для хранения данных между запросами в рамках транзакции
(в конце транзакции объект автоматически очищается).


## Переопределение контекста в своём приложении

Контекст можно переопределить в своём аппе. Для этого достаточно:

* создать класс наследник Context в `app/models/custom_context.py`

```python
from nlpf_statemachine.models import Context

class CustomContext(Context):
    ...
```

* определить его в классе наследнике `nlpf_statemachine.override.user.StateMachineAppsUser`
методом `nlpf_statemachine.override.user.StateMachineAppsUser.context_model` в `app/user.py`

```python
from nlpf_statemachine.override import StateMachineAppsUser
from app.models.custom_context import CustomContext

class CustomUser(StateMachineAppsUser):
    @property
    def context_model(self) -> None:
        return CustomContext
```

* Свой класс `CustomUser` необходимо определить я `app_config.py`.

```python
...
from app.user import CustomUser
...
USER = CustomUser
...
```

"""

from pydantic import BaseModel, Field

from .debug_info import CallHistoryItem
from .message import BaseMessage


class LocalContext(BaseModel):
    """Описание локального контекста (в рамках одной транзакции)."""

    init_event: str | None = Field(default=None)
    """Событие, с которого произошёл запуск ContextManager (может быть None, если был голосовой запуск)."""
    base_event: str | None = Field(default=None)
    """Базовое событие, с которого началась транзакция (событие, по которому был запущен первый экшен в транзакции)."""
    base_message: BaseMessage | None = Field(default=None)
    """Сообщение, с которого началась транзакция."""
    last_transaction_step_timestamp: float | None = Field(default=None)
    """Timestamp последнего запроса в транзакции."""
    call_history: list[CallHistoryItem | None] = Field(default_factory=list)
    """Список вызовов (полезное поле для отладки транзакции)."""
    character_id: str | None = Field(default=None)
    """Текущий выбранный ассистент."""
    run_isolated_scenario: bool | None = Field(default=False)
    """Флаг на запущенный изолированный сценарий."""
    isolated_scenario_id: str | None = Field(default=None)
    """Идентификатор запущенного изолированного сценария (если запущен)."""


class Context(BaseModel):
    """Описание контекста."""

    id: str | None = Field(default=None)
    """Идентификатор текущего стейта."""
    local: LocalContext = Field(default_factory=LocalContext)
    """Контекст, живущий в рамках одной транзакции (`LocalContext`)."""
    screen: str | None = Field(default=None)
    """Страница, на которой находится пользователь в рамках текущего запроса (если определена)."""
    event: str | None = Field(default=None)
    """Событие, на которое реагируем в текущем запросе."""
    last_screen: str | None = Field(default=None)
    """Страница, которая была при предыдущем запросе (обновляется в конце транзакции)."""
    last_event: str | None = Field(default=None)
    """Предыдущее событие."""
    last_response_message_name: str | None = Field(default=None)
    """Наименования предыдущего ответа."""
    last_intent: str | None = Field(default=None)
    """Последний пришедший интент от платформы."""

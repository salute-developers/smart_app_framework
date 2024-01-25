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
from typing import List, Optional

from pydantic import BaseModel, Field

from .debug_info import CallHistoryItem
from .message import BaseMessage


class LocalContext(BaseModel):
    """Описание локального контекста (в рамках одной транзакции)."""

    init_event: Optional[str] = None
    """Событие, с которого произошёл запуск ContextManager (может быть None, если был голосовой запуск)."""

    base_event: Optional[str] = None
    """Базовое событие, с которого началась транзакция (событие, по которому был запущен первый экшен в транзакции)."""

    base_message: Optional[BaseMessage] = None
    """Сообщение, с которого началась транзакция."""

    last_transaction_step_timestamp: Optional[float] = None
    """Timestamp последнего запроса в транзакции."""

    call_history: List[CallHistoryItem] = Field(default_factory=list)
    """Список вызовов (полезное поле для отладки транзакции)."""

    character_id: Optional[str]
    """Текущий выбранный ассистент."""

    run_isolated_scenario: Optional[bool] = False
    """Флаг на запущенный изолированный сценарий."""

    isolated_scenario_id: Optional[str] = None
    """Идентификатор запущенного изолированного сценария (если запущен)."""


class Context(BaseModel):
    """Описание контекста."""

    local: LocalContext = Field(default_factory=LocalContext)
    """Контекст, живущий в рамках одной транзакции (`LocalContext`)."""

    id: Optional[str] = None
    """Идентификатор текущего стейта."""

    screen: Optional[str] = None
    """Страница, на которой находится пользователь в рамках текущего запроса (если определена)."""

    event: Optional[str] = None
    """Событие, на которое реагируем в текущем запросе."""

    last_screen: Optional[str] = None
    """Страница, которая была при предыдущем запросе (обновляется в конце транзакции)."""

    last_event: Optional[str] = None
    """Предыдущее событие."""

    last_response_message_name: Optional[str] = None
    """Наименования предыдущего ответа."""

    last_intent: Optional[str] = None
    """Последний пришедший интент от платформы."""

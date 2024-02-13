"""
# Информация о событии и его параметры.

(может так же использоваться при запуске)
"""
from typing import Optional, Dict
from pydantic import BaseModel, Field

from .app_info import AppInfo


class ServerAction(BaseModel):
    """
    # Описание модели ServerAction.
    """

    action_id: str
    """
    Действие, которое обрабатывает бэкенд смартапа.
    Значение по умолчанию для запуска: *run_app*.
    """
    app_info: Optional[AppInfo] = Field(default=None)
    """Информация о смартапе."""
    parameters: Optional[Dict] = Field(default=None)
    """
    Любые параметры, которые требуются для запуска смартапа.
    Параметры должны быть представлены в виде валидного JSON-объекта.
    """

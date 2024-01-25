"""
# Информация о событии и его параметры.

(может так же использоваться при запуске)
"""
from typing import Dict, Optional

from pydantic import BaseModel

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
    app_info: Optional[AppInfo]
    """Информация о смартапе."""
    parameters: Optional[Dict]
    """
    Любые параметры, которые требуются для запуска смартапа.
    Параметры должны быть представлены в виде валидного JSON-объекта.
    """

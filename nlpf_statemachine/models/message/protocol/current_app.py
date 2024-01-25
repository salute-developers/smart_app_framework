"""
# Описание модели CurrentApp.
"""
from typing import Optional

from pydantic import BaseModel

from .app_info import AppInfo
from .item_selector import ItemSelector


class AssistantState(BaseModel):
    """
    # Описание модели AssistantState.

    Стейт фронта пришедшего запроса.

    *Данный класс необходимо переопределять в конкретных приложениях.*
    """

    screen: Optional[str]  # на запуске может не быть!
    item_selector: Optional[ItemSelector]


class CurrentApp(BaseModel):
    """
    # Описание модели CurrentApp.
    """

    app_info: Optional[AppInfo]
    state: Optional[AssistantState]

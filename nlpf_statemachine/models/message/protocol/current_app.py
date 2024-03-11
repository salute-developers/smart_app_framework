"""
# Описание модели CurrentApp.
"""
from typing import Optional

from pydantic import BaseModel, Field

from .app_info import AppInfo
from .item_selector import ItemSelector


class AssistantState(BaseModel):
    """
    # Описание модели AssistantState.

    Стейт фронта пришедшего запроса.

    *Данный класс необходимо переопределять в конкретных приложениях.*
    """

    screen: Optional[str] = Field(default=None)
    item_selector: Optional[ItemSelector] = Field(default=None)


class CurrentApp(BaseModel):
    """
    # Описание модели CurrentApp.
    """

    app_info: Optional[AppInfo] = Field(default=None)
    state: Optional[AssistantState] = Field(default=None)

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

    screen: str | None = Field(default=None)
    item_selector: ItemSelector | None = Field(default=None)


class CurrentApp(BaseModel):
    """
    # Описание модели CurrentApp.
    """

    app_info: AppInfo | None = Field(default=None)
    state: AssistantState | None = Field(default=None)

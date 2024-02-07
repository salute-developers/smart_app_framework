"""
# Данные о содержимом экрана пользователя.
"""
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field

from .current_app import CurrentApp


class MetaTime(BaseModel):
    """
    # Описание модели Time.

    Данные о текущем времени на устройстве пользователя
    """

    timestamp: int | None = Field(default=None)
    """Unix-время в миллисекундах."""
    timezone_id: str | None = Field(default=None)
    """Наименование часового пояса. Пример Europe/Moscow"""
    timezone_offset_sec: int | None = Field(default=None)
    """Наименование часового пояса. Пример Europe/Moscow."""


class MetaFeature(BaseModel):
    """
    # Описание модели MetaFeature.

    Признака фичи.
    """

    enabled: bool | None = Field(default=None)
    """Флаг доступности фичи."""


class MetaFeatures(BaseModel):
    """
    # Описание модели Time.

    Данные о текущем времени на устройстве пользователя
    """

    screen: MetaFeature | None = Field(default=None)
    """признак включенного экрана на устройстве."""
    int_login: MetaFeature | None = Field(default=None)
    """авторизован ли пользователь на устройстве."""


class MetaLocation(BaseModel):
    """
    # Описание модели location в meta в запросе.
    """

    accuracy: float | None = Field(default=None)
    """Точность"""
    lat: float | None = Field(default=None)
    """Широта"""
    lon: float | None = Field(default=None)
    """Долгота"""
    source: str | None = Field(default=None)
    """Источник"""
    timestamp: int | None = Field(default=None)
    """Время"""


class AssistantMeta(BaseModel):
    """
    # Описание модели AssistantMeta.

    Данные о содержимом экрана пользователя.
    """

    time: MetaTime | None = Field(default=None)
    """
    Данные о текущем времени на устройстве пользователя.

    Содержит следующие поля:

    timestamp — число. Unix-время в миллисекундах.
    timezone_id — строка. Наименование часового пояса. Пример Europe/Moscow.
    timezone_offset_sec — число.
    """
    features: MetaFeatures | None = Field(default=None)
    """Данные о режиме работы устройства."""
    current_app: CurrentApp | None = Field(default=None)
    """Информация о текущем аппе."""
    host_meta: dict | None = Field(default=None)
    """
    Произвольный JSON-объект, который заполняет хост приложение, в которое встроено Assistant SDK.
    Например 2gis, будет заполнять координаты, текущий экран, регион и другие данные, которые доступны в приложении 2gis
    """
    mobile_sdk_data: str | None = Field(default=None)
    """Данные для анти-фрода, закодировааные в base64-строку"""
    network: dict | None = Field(default=None)
    """Информация о сети"""
    user_settings: dict | None = Field(default=None)
    """Пользовательские настройки"""
    location: MetaLocation | None = Field(default=None)
    """Данные о расположении устройства"""
    experimental_flags: dict | None = Field(default=None)
    """Параметры сети"""
    volume: dict | None = Field(default=None)
    """Информация о громкости"""
    start_audio_recording_source: str | None = Field(default=None)
    """Откуда был инициирован голосовой запрос, например в приложении 2gis есть две точки входа,
    для разных точек входа тут будет разные значения"""
    background_apps: dict | None = Field(default=None)
    """Фоновые приложения"""
    installed_apps: dict | None = Field(default=None)
    """Установленные приложения"""
    capabilities_state: dict | None = Field(default=None)
    """Стейт внешних устройств"""

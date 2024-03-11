"""
# Данные о содержимом экрана пользователя.
"""
from typing import Dict, Optional

from pydantic import BaseModel, Field

from .current_app import CurrentApp


class MetaTime(BaseModel):
    """
    # Описание модели Time.

    Данные о текущем времени на устройстве пользователя
    """

    timestamp: Optional[int] = Field(default=None)
    """Unix-время в миллисекундах."""
    timezone_id: Optional[str] = Field(default=None)
    """Наименование часового пояса. Пример Europe/Moscow"""
    timezone_offset_sec: Optional[int] = Field(default=None)
    """Наименование часового пояса. Пример Europe/Moscow."""


class MetaFeature(BaseModel):
    """
    # Описание модели MetaFeature.

    Признака фичи.
    """

    enabled: Optional[bool] = Field(default=None)
    """Флаг доступности фичи."""


class MetaFeatures(BaseModel):
    """
    # Описание модели Time.

    Данные о текущем времени на устройстве пользователя
    """

    screen: Optional[MetaFeature] = Field(default=None)
    """признак включенного экрана на устройстве."""
    int_login: Optional[MetaFeature] = Field(default=None)
    """авторизован ли пользователь на устройстве."""


class MetaLocation(BaseModel):
    """
    # Описание модели location в meta в запросе.
    """

    accuracy: Optional[float] = Field(default=None)
    """Точность"""
    lat: Optional[float] = Field(default=None)
    """Широта"""
    lon: Optional[float] = Field(default=None)
    """Долгота"""
    source: Optional[str] = Field(default=None)
    """Источник"""
    timestamp: Optional[int] = Field(default=None)
    """Время"""


class AssistantMeta(BaseModel):
    """
    # Описание модели AssistantMeta.

    Данные о содержимом экрана пользователя.
    """

    time: Optional[MetaTime] = Field(default=None)
    """
    Данные о текущем времени на устройстве пользователя.

    Содержит следующие поля:

    timestamp — число. Unix-время в миллисекундах.
    timezone_id — строка. Наименование часового пояса. Пример Europe/Moscow.
    timezone_offset_sec — число.
    """
    features: Optional[MetaFeatures] = Field(default=None)
    """Данные о режиме работы устройства."""
    current_app: Optional[CurrentApp] = Field(default=None)
    """Информация о текущем аппе."""
    host_meta: Optional[Dict] = Field(default=None)
    """
    Произвольный JSON-объект, который заполняет хост приложение, в которое встроено Assistant SDK.
    Например 2gis, будет заполнять координаты, текущий экран, регион и другие данные, которые доступны в приложении 2gis
    """
    mobile_sdk_data: Optional[str] = Field(default=None)
    """Данные для анти-фрода, закодировааные в base64-строку"""
    network: Optional[Dict] = Field(default=None)
    """Информация о сети"""
    user_settings: Optional[Dict] = Field(default=None)
    """Пользовательские настройки"""
    location: Optional[MetaLocation] = Field(default=None)
    """Данные о расположении устройства"""
    experimental_flags: Optional[Dict] = Field(default=None)
    """Параметры сети"""
    volume: Optional[Dict] = Field(default=None)
    """Информация о громкости"""
    start_audio_recording_source: Optional[str] = Field(default=None)
    """Откуда был инициирован голосовой запрос, например в приложении 2gis есть две точки входа,
    для разных точек входа тут будет разные значения"""
    background_apps: Optional[Dict] = Field(default=None)
    """Фоновые приложения"""
    installed_apps: Optional[Dict] = Field(default=None)
    """Установленные приложения"""
    capabilities_state: Optional[Dict] = Field(default=None)
    """Стейт внешних устройств"""

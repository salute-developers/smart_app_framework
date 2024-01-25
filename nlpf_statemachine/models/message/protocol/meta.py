"""
# Данные о содержимом экрана пользователя.
"""
from typing import Any, Dict, Optional

from pydantic import BaseModel

from .current_app import CurrentApp


class MetaTime(BaseModel):
    """
    # Описание модели Time.

    Данные о текущем времени на устройстве пользователя
    """

    timestamp: Optional[int]
    """Unix-время в миллисекундах."""
    timezone_id: Optional[str]
    """Наименование часового пояса. Пример Europe/Moscow"""
    timezone_offset_sec: Optional[int]
    """Наименование часового пояса. Пример Europe/Moscow."""


class MetaFeature(BaseModel):
    """
    # Описание модели MetaFeature.

    Признака фичи.
    """

    enabled: Optional[bool]
    """Флаг доступности фичи."""


class MetaFeatures(BaseModel):
    """
    # Описание модели Time.

    Данные о текущем времени на устройстве пользователя
    """

    screen: Optional[MetaFeature]
    """признак включенного экрана на устройстве."""
    int_login: Optional[MetaFeature]
    """авторизован ли пользователь на устройстве."""


class MetaLocation(BaseModel):
    """
    # Описание модели location в meta в запросе.
    """

    accuracy: Optional[float]
    """Точность"""
    lat: Optional[float]
    """Широта"""
    lon: Optional[float]
    """Долгота"""
    source: Optional[str]
    """Источник"""
    timestamp: Optional[int]
    """Время"""


class AssistantMeta(BaseModel):
    """
    # Описание модели AssistantMeta.

    Данные о содержимом экрана пользователя.
    """

    time: Optional[MetaTime]
    """
    Данные о текущем времени на устройстве пользователя.

    Содержит следующие поля:

    timestamp — число. Unix-время в миллисекундах.
    timezone_id — строка. Наименование часового пояса. Пример Europe/Moscow.
    timezone_offset_sec — число.
    """
    features: Optional[MetaFeatures]
    """Данные о режиме работы устройства."""
    current_app: Optional[CurrentApp]
    """Информация о текущем аппе."""
    host_meta: Optional[Dict[str, Any]]
    """
    Произвольный JSON-объект, который заполняет хост приложение, в которое встроено Assistant SDK.
    Например 2gis, будет заполнять координаты, текущий экран, регион и другие данные, которые доступны в приложении 2gis
    """
    mobile_sdk_data: Optional[str]
    """Данные для анти-фрода, закодировааные в base64-строку"""
    network: Optional[Dict[str, Any]]
    """Информация о сети"""
    user_settings: Optional[Dict[str, Any]]
    """Пользовательские настройки"""
    location: Optional[MetaLocation]
    """Данные о расположении устройства"""
    experimental_flags: Optional[Dict[str, Any]]
    """Параметры сети"""
    volume: Optional[Dict[str, Any]]
    """Информация о громкости"""
    start_audio_recording_source: Optional[str]
    """Откуда был инициирован голосовой запрос, например в приложении 2gis есть две точки входа,
    для разных точек входа тут будет разные значения"""
    background_apps: Optional[Dict[str, Any]]
    """Фоновые приложения"""
    installed_apps: Optional[Dict[str, Any]]
    """Установленные приложения"""
    capabilities_state: Optional[Dict[str, Any]]
    """Стейт внешних устройств"""

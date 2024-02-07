"""
# Описание модели Device.
"""
from typing import Any

from pydantic import BaseModel, Field

from .device_capability import DeviceCapabilities
from .device_features import DeviceFeatures


class Device(BaseModel):
    """
    # Описание модели Device.
    """

    platformType: str | None = Field(default=None)
    """
    Операционная система устройства.

    Возможные значения:

    * ANDROID;
    * IOS.
    """
    platformVersion: str | None = Field(default=None)
    """Версия операционной системы."""
    surface: str | None = Field(default=None)
    """
    Устройство или мобильное приложение, от которого приходит вызов ассистента.

    Возможные значения:

    * SBERBOX — запрос пришел от устройства SberBox;
    * COMPANION — запрос от приложения Салют;
    * STARGATE — запрос от устройства SberPortal.
    """
    surfaceVersion: str | None = Field(default=None)
    """Версия поверхности."""
    deviceId: str | None = Field(default=None)
    """Идентификатор устройства."""
    features: DeviceFeatures | None = Field(default=None)
    """Описание функциональности устройства."""
    capabilities: DeviceCapabilities | None = Field(default=None)
    """Описание возможностей устройства пользователя."""
    additionalInfo: Any | None = Field(default=None)
    """Дополнительная информация об объекте или устройстве. В настоящий момент не используется."""
    deviceManufacturer: str | None = Field(default=None)
    """Производитель устройства"""
    deviceModel: str | None = Field(default=None)
    """Модель устройства"""

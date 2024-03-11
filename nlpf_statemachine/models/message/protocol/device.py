"""
# Описание модели Device.
"""
from typing import Any, Optional

from pydantic import BaseModel, Field

from .device_capability import DeviceCapabilities
from .device_features import DeviceFeatures


class Device(BaseModel):
    """
    # Описание модели Device.
    """

    platformType: Optional[str] = Field(default=None)
    """
    Операционная система устройства.

    Возможные значения:

    * ANDROID;
    * IOS.
    """
    platformVersion: Optional[str] = Field(default=None)
    """Версия операционной системы."""
    surface: Optional[str] = Field(default=None)
    """
    Устройство или мобильное приложение, от которого приходит вызов ассистента.

    Возможные значения:

    * SBERBOX — запрос пришел от устройства SberBox;
    * COMPANION — запрос от приложения Салют;
    * STARGATE — запрос от устройства SberPortal.
    """
    surfaceVersion: Optional[str] = Field(default=None)
    """Версия поверхности."""
    deviceId: Optional[str] = Field(default=None)
    """Идентификатор устройства."""
    features: Optional[DeviceFeatures] = Field(default=None)
    """Описание функциональности устройства."""
    capabilities: Optional[DeviceCapabilities] = Field(default=None)
    """Описание возможностей устройства пользователя."""
    additionalInfo: Optional[Any] = Field(default=None)
    """Дополнительная информация об объекте или устройстве. В настоящий момент не используется."""
    deviceManufacturer: Optional[str] = Field(default=None)
    """Производитель устройства"""
    deviceModel: Optional[str] = Field(default=None)
    """Модель устройства"""

"""
# Описание модели Device.
"""
from typing import Any, Optional

from pydantic import BaseModel

from .device_capability import DeviceCapabilities
from .device_features import DeviceFeatures


class Device(BaseModel):
    """
    # Описание модели Device.
    """

    platformType: Optional[str]
    """
    Операционная система устройства.

    Возможные значения:

    * ANDROID;
    * IOS.
    """
    platformVersion: Optional[str]
    """Версия операционной системы."""
    surface: Optional[str]
    """
    Устройство или мобильное приложение, от которого приходит вызов ассистента.

    Возможные значения:

    * SBERBOX — запрос пришел от устройства SberBox;
    * COMPANION — запрос от приложения Салют;
    * STARGATE — запрос от устройства SberPortal.
    """
    surfaceVersion: Optional[str]
    """Версия поверхности."""
    deviceId: Optional[str]
    """Идентификатор устройства."""
    features: Optional[DeviceFeatures]
    """Описание функциональности устройства."""
    capabilities: Optional[DeviceCapabilities]
    """Описание возможностей устройства пользователя."""
    additionalInfo: Optional[Any]
    """Дополнительная информация об объекте или устройстве. В настоящий момент не используется."""
    deviceManufacturer: Optional[str]
    """Производитель устройства"""
    deviceModel: Optional[str]
    """Модель устройства"""

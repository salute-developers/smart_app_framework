"""
# Описание возможностей устройства пользователя.
"""
from typing import Optional

from pydantic import BaseModel


class DeviceCapability(BaseModel):
    """
    # Описание модели DeviceCapability.
    """

    available: Optional[bool]
    """Флаг наличия возможностию"""


class DeviceCapabilities(BaseModel):
    """
    # Описание модели DeviceCapabilities.
    """

    screen: Optional[DeviceCapability]
    """Описание экрана устройства."""
    mic: Optional[DeviceCapability]
    """Описание микрофона устройства."""
    speak: Optional[DeviceCapability]
    """Описание динамиков устройства."""

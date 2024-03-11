"""
# Описание возможностей устройства пользователя.
"""
from typing import Optional

from pydantic import BaseModel, Field


class DeviceCapability(BaseModel):
    """
    # Описание модели DeviceCapability.
    """

    available: Optional[bool] = Field(default=None)
    """Флаг наличия возможностию"""


class DeviceCapabilities(BaseModel):
    """
    # Описание модели DeviceCapabilities.
    """

    screen: Optional[DeviceCapability] = Field(default=None)
    """Описание экрана устройства."""
    mic: Optional[DeviceCapability] = Field(default=None)
    """Описание микрофона устройства."""
    speak: Optional[DeviceCapability] = Field(default=None)
    """Описание динамиков устройства."""

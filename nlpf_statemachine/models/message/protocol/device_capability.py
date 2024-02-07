"""
# Описание возможностей устройства пользователя.
"""

from pydantic import BaseModel, Field


class DeviceCapability(BaseModel):
    """
    # Описание модели DeviceCapability.
    """

    available: bool | None = Field(default=None)
    """Флаг наличия возможностию"""


class DeviceCapabilities(BaseModel):
    """
    # Описание модели DeviceCapabilities.
    """

    screen: DeviceCapability | None = Field(default=None)
    """Описание экрана устройства."""
    mic: DeviceCapability | None = Field(default=None)
    """Описание микрофона устройства."""
    speak: DeviceCapability | None = Field(default=None)
    """Описание динамиков устройства."""

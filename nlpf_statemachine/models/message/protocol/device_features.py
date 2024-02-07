"""
Описание функциональности устройства.
"""

from pydantic import BaseModel, Field

from nlpf_statemachine.models.enums import DeviceFeaturesAppTypes


class DeviceFeatures(BaseModel):
    """
    # Описание модели DeviceFeatures.
    """

    appTypes: list[DeviceFeaturesAppTypes | str] | None = Field(default=None)
    """
    Типы смартапов, которые поддерживает устройство.

    Возможные значения:

    * DIALOG;
    * WEB_APP;
    * APK;
    * CHAT_APP.
    * EMBEDDED_APP
    * ...
    """
    clientFlags: dict | None = Field(default={})
    """Описание клиентских флагов"""

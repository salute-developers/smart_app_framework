"""
Описание функциональности устройства.
"""
from typing import List, Optional, Union, Dict, Any

from pydantic import BaseModel

from nlpf_statemachine.models.enums import DeviceFeaturesAppTypes


class DeviceFeatures(BaseModel):
    """
    # Описание модели DeviceFeatures.
    """

    appTypes: Optional[List[Union[DeviceFeaturesAppTypes, str]]]
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
    clientFlags: Optional[Dict[str, Any]] = {}
    """Описание клиентских флагов"""

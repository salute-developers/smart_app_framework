"""
# Типы аппов.
"""
from .smart_enum import SmartEnum


class DeviceFeaturesAppTypes(SmartEnum):
    """
    # Enum с типами аппов.
    """

    DIALOG = "DIALOG"
    WEB_APP = "WEB_APP"
    APK = "APK"
    CHAT_APP = "CHAT_APP"
    EMBEDDED_APP = "EMBEDDED_APP"

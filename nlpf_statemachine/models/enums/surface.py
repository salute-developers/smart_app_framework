"""
# Устройство или мобильное приложение, от которого приходит вызов ассистента.

Множество всех поверхностей описано тут: https://confluence.sberbank.ru/pages/viewpage.action?pageId=6412830553
"""
from .smart_enum import SmartEnum


class Surface(SmartEnum):
    """
    # Устройство или мобильное приложение, от которого приходит вызов ассистента.
    """

    SBERBOX = "SBERBOX"
    """Устройство SberBox."""
    COMPANION = "COMPANION"
    """МП Салют."""
    STARGATE = "STARGATE"
    """Устройство SberPortal."""
    SBOL = "SBOL"
    """Сбербанк-онлайн."""
    WEB = "WEB"
    """Виртуальный ассистент на поверхности web-СБОЛа."""
    SUPER_APP = "SUPER_APP"
    """Супер-Апп. Канал SUPER_APP."""
    DEMO_APP = "DEMO_APP"
    """Демо-апп. Канал FEBRUARY."""
    SOMMELIER = "SOMMELIER"
    """МП Сомелье (навык с собственной поверхностью)."""
    TV = "TV"
    """Умные телевизоры Салют ТВ."""
    TV_HUAWEI = "TV_HUAWEI"
    """Умные телевизоры Huawei."""
    SATELLITE = "SATELLITE"
    """Устройство SberBox Top."""
    TIME = "TIME"
    """Устройство SberBox Time."""
    SBERBOOM = "SBERBOOM"
    """Устройство SBERBOOM."""
    SBERBOOM_MINI = "SBERBOOM_MINI"
    """Устройство SBERBOOM_MINI."""
    SAMSUNG_TV = "SAMSUNG_TV"
    """Умные телевизоры Samsung."""
    HUAWEI_KIDS_WATCH = "HUAWEI_KIDS_WATCH"
    """Умные детские часы Huawei Watch."""
    SBER_RU_WEB = "SBER_RU_WEB"
    """WEB-версия МП Салют на домене sber.ru."""
    TWO_GIS = "2GIS"
    """МП 2GIS."""

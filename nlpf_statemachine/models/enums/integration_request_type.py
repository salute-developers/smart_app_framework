"""
# Возможные способы интеграций.
"""
from .smart_enum import SmartEnum


class IntegrationRequestType(SmartEnum):
    """
    # Список способов интегрироваться.

    На текущий момент доступна только kafka.
    (будет расширяться)
    """

    KAFKA = "kafka"

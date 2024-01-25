"""
# Enum-ы для описания ассистентов.
"""
from .smart_enum import SmartEnum


class AssistantName(SmartEnum):
    """
    # Имена ассистентов.
    """

    sber = "Сбер"
    athena = "Афина"
    joy = "Джой"


class AssistantId(SmartEnum):
    """
    # Id ассистентов.
    """

    sber = "sber"
    athena = "eva"
    joy = "joy"


class AssistantGender(SmartEnum):
    """
    # Пол ассистентов.
    """

    male = "male"
    female = "female"


class AssistantAppeal(SmartEnum):
    """
    # Стиль общения ассистентов.
    """

    official = "official"
    no_official = "no_official"

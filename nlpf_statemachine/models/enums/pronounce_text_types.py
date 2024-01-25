"""
# Возможные способы сформировать голосовой ответ.
"""
from .smart_enum import SmartEnum


class PronounceTextType(SmartEnum):
    """
    # Список способов сформировать голосовой ответ.
    """

    TEXT = "application/text"
    SSML = "application/ssml"

"""
# Системные события, которые могут произойти.
"""
from .smart_enum import SmartEnum


class Event(SmartEnum):
    """
    # Список событий.
    """

    LOCAL_TIMEOUT = "LOCAL_TIMEOUT"
    ERROR = "ERROR"
    FALLBACK = "FALLBACK"

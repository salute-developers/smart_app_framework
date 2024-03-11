"""
# Наименования базовых запросов.
"""
from .smart_enum import SmartEnum


class RequestMessageName(SmartEnum):
    """
    # Enum с наименованиями базовых запросов.
    """

    MESSAGE_TO_SKILL = "MESSAGE_TO_SKILL"
    SERVER_ACTION = "SERVER_ACTION"
    RUN_APP = "RUN_APP"
    CLOSE_APP = "CLOSE_APP"


class ResponseMessageName(SmartEnum):
    """
    # Enum с наименованиями базовых ответов.
    """

    ANSWER_TO_USER = "ANSWER_TO_USER"
    POLICY_RUN_APP = "POLICY_RUN_APP"
    NOTHING_FOUND = "NOTHING_FOUND"
    DO_NOTHING = "DO_NOTHING"
    ERROR = "ERROR"

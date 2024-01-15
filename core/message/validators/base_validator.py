from __future__ import annotations
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, TypeVar, Literal, Union
from core.logging.logger_utils import log, MESSAGE_ID_STR

if TYPE_CHECKING:
    from core.message.message import SmartAppMessage


class ValidationException(Exception):
    pass


T = TypeVar("T", bound=Exception)
OnException = Literal["raise", "log"]


class BaseMessageValidator(ABC):
    VALIDATOR_EXCEPTION: T = ValidationException

    def __init__(self, on_exception: OnException = "raise", *args, **kwargs):
        self.on_exception = on_exception

    def validate(self, message: SmartAppMessage):
        try:
            self._validate(message)
        except self.VALIDATOR_EXCEPTION as e:
            if self.on_exception == "log":
                self._log(e, message)
            if self.on_exception == "raise":
                self._log(e, message, level="ERROR")
                raise

    def _log_params(self, message: SmartAppMessage):
        try:
            mid = message.incremental_id
        except KeyError:
            mid = None
        return {
            "key_name": "message_validator",
            MESSAGE_ID_STR: mid,
            "message_name": message.message_name,
            "validator": self.__class__.__name__,
        }

    def _log(self, exception: VALIDATOR_EXCEPTION, message: SmartAppMessage, level="WARNING"):
        log_params = self._log_params(message)
        log(f"{self.__class__.__name__} Error: {exception}", params=log_params, level=level)

    @abstractmethod
    def _validate(self, message: SmartAppMessage):
        raise NotImplementedError

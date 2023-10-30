from __future__ import annotations
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, TypeVar, Literal
from core.logging.logger_utils import log

if TYPE_CHECKING:
    from core.message.from_message import SmartAppFromMessage


class ValidationException(Exception):
    pass


T = TypeVar("T", bound=Exception)
OnException = Literal["raise", "log"]


class BaseMessageValidator(ABC):
    VALIDATOR_EXCEPTION: T = ValidationException

    def __init__(self, on_exception: OnException = "raise"):
        self.on_exception = on_exception

    def validate(self, message: SmartAppFromMessage):
        try:
            self._validate(message)
        except self.VALIDATOR_EXCEPTION as e:
            if self.on_exception == "log":
                log(f"{self.__class__.__name__} Error: {e}")
            else:
                raise

    @abstractmethod
    def _validate(self, message: SmartAppFromMessage):
        raise NotImplementedError

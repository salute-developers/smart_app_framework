from abc import ABC, abstractmethod
from typing import Iterable

from core.message.validators.base_validator import BaseMessageValidator


class SmartAppMessage(ABC):
    MESSAGE_ID = "messageId"

    def __init__(self, validators: Iterable[BaseMessageValidator] = (), *args, **kwargs):
        self.validators = validators

    def validate(self) -> bool:
        for validator in self.validators:
            try:
                validator.validate(self)
            except validator.VALIDATOR_EXCEPTION:  # FIXME: убрать return, ловить эксепшны в лупе
                return False
        return True

    @property
    @abstractmethod
    def payload(self):
        ...

    @property
    @abstractmethod
    def as_dict(self):
        ...

    # unique message_id
    @property
    def incremental_id(self) -> int:
        return self.as_dict[self.MESSAGE_ID]
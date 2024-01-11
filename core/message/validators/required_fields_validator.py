from __future__ import annotations
from typing import Dict, Optional, Iterable, TYPE_CHECKING

from core.message.validators.base_validator import BaseMessageValidator, OnException, ValidationException
from core.message.message_constants import MESSAGE_ID, UUID, PAYLOAD, SESSION_ID, MESSAGE_NAME

if TYPE_CHECKING:
    from core.message.message import SmartAppMessage


class RequiredFieldsValidator(BaseMessageValidator):
    DEFAULT_REQUIRED_FIELDS: Dict[Optional[str], Iterable[str]] = {
        None: {MESSAGE_ID, UUID, PAYLOAD, SESSION_ID, MESSAGE_NAME},  # default
        "PUSH_RESULT": {MESSAGE_ID, MESSAGE_NAME},
        "PUSH_SENDING_RESULT": {MESSAGE_ID, MESSAGE_NAME}
    }
    DEFAULT_FIELD_TYPES: Dict[str, type] = {
        MESSAGE_ID: int,
        MESSAGE_NAME: str,
        PAYLOAD: dict,
        UUID: dict,
    }

    def __init__(self, required_fields: Optional[Dict[Optional[str], Iterable[str]]] = None,
                 field_types: Optional[Dict[str, type]] = None,
                 on_exception: OnException = "raise",
                 *args, **kwargs):
        super().__init__(on_exception)
        if required_fields is None:
            required_fields = {}
        required_fields.setdefault(None, [])
        self._required_fields = required_fields or self.DEFAULT_REQUIRED_FIELDS
        self._field_types = field_types or self.DEFAULT_FIELD_TYPES

    def _validate(self, message: SmartAppMessage):
        message_name = message.message_name
        required_fields = self._required_fields.get(message_name) or self._required_fields[None]
        for r_field in required_fields:
            if r_field not in message.as_dict:
                raise ValidationException(f"Required field '{r_field}' is absent")
            if r_field in self._field_types and \
                    not isinstance(message.as_dict[r_field], self._field_types[r_field]):  # noqa
                raise ValidationException(f"Field '{r_field}' has wrong type "
                                          f"(required {self._field_types[r_field]})")

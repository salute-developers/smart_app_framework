from __future__ import annotations
from typing import TYPE_CHECKING
from core.message.validators.base_validator import BaseMessageValidator, ValidationException

if TYPE_CHECKING:
    from core.message.from_message import SmartAppFromMessage


class MessageHeadersValidator(BaseMessageValidator):
    def _validate(self, message: SmartAppFromMessage):
        if message._headers_required and not message.headers:
            raise ValidationException("Message headers is empty")

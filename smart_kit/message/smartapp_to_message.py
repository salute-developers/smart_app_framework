from __future__ import annotations

from functools import cached_property
from typing import TYPE_CHECKING, Iterable, Optional, List
import json
from copy import copy

from core.utils.masking_message import masking
from core.utils.utils import mask_numbers
from smart_kit.configs import settings

if TYPE_CHECKING:
    from core.basic_models.actions.command import Command
    from core.message.msg_validator import MessageValidator
    from smart_kit.request.kafka_request import SmartKitKafkaRequest


class SmartAppToMessage:
    ROOT_NODES_KEY = "root_nodes"
    PAYLOAD = "payload"

    def __init__(self, command: Command, message, request: SmartKitKafkaRequest,
                 forward_fields=None, masking_fields=None, validators: Iterable[MessageValidator] = (),
                 masking_white_list: Optional[List[str]] = None, **kwargs):
        root_nodes = command.payload.pop(self.ROOT_NODES_KEY, None)
        self.command = command
        self.root_nodes = root_nodes or {}
        self.incoming_message = message
        self.request = request
        self.forward_fields = forward_fields or ()
        self.masking_fields = masking_fields
        self.masking_white_list = masking_white_list
        self.validators = validators
        self._kwargs = kwargs

    @cached_property
    def payload(self):
        payload = copy(self.command.payload)
        for field in self.forward_fields:
            if field not in self.incoming_message.payload:
                continue
            if field in payload:
                continue
            payload[field] = self.incoming_message.payload[field]
        return payload

    @cached_property
    def as_dict(self):
        fields = {
            "messageId": self.incoming_message.incremental_id,
            "sessionId": self.incoming_message.session_id,
            "messageName": self.command.name,
            "payload": self.payload,
            "uuid": self.incoming_message.uuid
        }
        fields.update(self.root_nodes)
        return fields


    @cached_property
    def masked_value(self):
        mask_numbers_flag = settings.Settings()["template_settings"].get("mask_numbers", False)
        masked_data = mask_numbers(masking(self.as_dict, self.masking_fields)) if mask_numbers_flag else \
            masking(self.as_dict, self.masking_fields)
        if self.command.loader == "json.dumps":
            return json.dumps(masked_data, ensure_ascii=False)


    @cached_property
    def value(self):
        if self.command.loader == "json.dumps":
            return json.dumps(self.as_dict, ensure_ascii=False)

    def validate(self):
        for validator in self.validators:
            if not validator.validate(self.command.name, self.payload):
                return False
        return True

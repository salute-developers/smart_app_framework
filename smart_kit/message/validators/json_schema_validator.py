from __future__ import annotations
from typing import Callable, TYPE_CHECKING

import fastjsonschema
import jsonschema
from smart_kit.message.validators.base_validator_with_resources import BaseMessageValidatorWithResources

if TYPE_CHECKING:
    from core.message.from_message import SmartAppFromMessage


class JSONSchemaValidator(BaseMessageValidatorWithResources):
    VALIDATOR_EXCEPTION = jsonschema.ValidationError

    def _update_resources(self):
        schemas = self.resources.get("payload_schema")
        self._schemas = {k: self._compile_schema(v) for k, v in schemas.items()}

    @staticmethod
    def _compile_schema(schema: dict) -> Callable[[dict], None]:
        cls = jsonschema.validators.validator_for(schema)
        cls.check_schema(schema)
        instance = cls(schema)
        return instance.validate

    def _validate(self, message: SmartAppFromMessage):
        validator = self._schemas.get(message.message_name)
        validator(message.payload)


class FastJSONSchemaValidator(JSONSchemaValidator):
    VALIDATOR_EXCEPTION = fastjsonschema.JsonSchemaValueException

    @staticmethod
    def _compile_schema(schema: dict) -> Callable[[dict], None]:
        return fastjsonschema.compile(schema)

from __future__ import annotations
from typing import Callable, TYPE_CHECKING

import fastjsonschema
import jsonschema

from core.message.message import SmartAppMessage
from core.logging.logger_utils import log
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

    def _log(self, exception: VALIDATOR_EXCEPTION, message: SmartAppMessage, level="WARNING"):
        log_params = self._log_params(message)
        log_params["json_path"] = exception.json_path
        log(f"{self.__class__.__name__} Error: {exception.message} on path: {exception.json_path}", params=log_params,
            level=level)

    def _validate(self, message: SmartAppFromMessage):
        validator = self._schemas.get(message.message_name)
        if validator:
            validator(message.payload)


class FastJSONSchemaValidator(JSONSchemaValidator):
    VALIDATOR_EXCEPTION = fastjsonschema.JsonSchemaValueException

    @staticmethod
    def _compile_schema(schema: dict) -> Callable[[dict], None]:
        return fastjsonschema.compile(schema)

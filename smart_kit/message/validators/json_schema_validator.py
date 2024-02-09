from __future__ import annotations

from pathlib import Path
from typing import Callable, TYPE_CHECKING, Optional
import jsonschema
from jsonschema.validators import RefResolver

from core.message.message import SmartAppMessage
from core.logging.logger_utils import log
from core.message.validators.base_validator import OnException
from smart_kit.message.validators.base_validator_with_resources import BaseMessageValidatorWithResources
from smart_kit.resources import SmartAppResources

if TYPE_CHECKING:
    from core.message.from_message import SmartAppFromMessage


class JSONSchemaValidator(BaseMessageValidatorWithResources):
    VALIDATOR_EXCEPTION = jsonschema.ValidationError

    def __init__(self, validator_group: str = "incoming",
                 resources: Optional[SmartAppResources] = None,
                 on_exception: OnException = "raise", *args, **kwargs):
        self._message_type = validator_group if validator_group in ("incoming", "outgoing") else "incoming"
        super().__init__(resources, on_exception, *args, **kwargs)

    def _update_resources(self):
        self._store = self.resources.get("payload_schema")
        self._schemas = {Path(k).stem: self._compile_schema(k, v) for k, v in self._store.items()
                         if k.startswith(f"/{self._message_type}/")}

    def _compile_schema(self, uri: str, schema: dict) -> Callable[[dict], None]:
        cls = jsonschema.validators.validator_for(schema)
        cls.check_schema(schema)
        instance = cls(schema, resolver=RefResolver(base_uri=uri, referrer=schema,
                                                    handlers={"": self._handle_includes}))
        return instance.validate

    def _handle_includes(self, path):
        return self._store[path]

    def _log(self, exception: VALIDATOR_EXCEPTION, message: SmartAppMessage, level="WARNING"):
        log_params = self._log_params(message)
        log_params["json_path"] = exception.json_path
        log(f"{self.__class__.__name__} Error: {exception.message} on path: {exception.json_path}", params=log_params,
            level=level)

    def _validate(self, message: SmartAppFromMessage):
        validator = self._schemas.get(message.message_name)
        if validator:
            validator(message.payload)

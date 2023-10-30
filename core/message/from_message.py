# coding=utf-8
from typing import Iterable, Dict, Optional, Set, Any, List, Union, Tuple
import json
import uuid

from core.configs.global_constants import CALLBACK_ID_HEADER
from core.message.app_info import AppInfo
from core.message.device import Device
from core.names import field
import core.logging.logger_constants as log_const
from core.logging.logger_utils import log
from core.utils.masking_message import masking
from core.utils.utils import current_time_ms
from core.message.msg_validator import MessageValidator

from smart_kit.configs import get_app_config


class Headers:
    def __init__(self, data):
        self.raw = dict(data)

    def __getitem__(self, item):
        return self.raw[item].decode()

    def __contains__(self, item):
        return item in self.raw

    def get(self, key, default=None, encoding="utf-8"):
        res = self.raw.get(key)
        if res is None:
            return default
        return res.decode(encoding=encoding)

    def __bool__(self):
        return bool(self.raw)


class SmartAppFromMessage:
    MESSAGE_NAME = "messageName"
    MESSAGE_ID = "messageId"
    UUID = "uuid"
    PAYLOAD = "payload"
    SESSION_ID = "sessionId"
    CALLBACK_ID_HEADER_NAME = CALLBACK_ID_HEADER

    _REQUIRED_FIELDS_MAP = {
        None: {MESSAGE_ID, UUID, PAYLOAD, SESSION_ID, MESSAGE_NAME},  # default
        "PUSH_RESULT": {MESSAGE_ID, MESSAGE_NAME},
        "PUSH_SENDING_RESULT": {MESSAGE_ID, MESSAGE_NAME}
    }

    # following fields are used for validation
    incremental_id: int
    message_name: str
    payload: dict
    uuid: dict

    def __init__(self, value: Dict[str, Any], topic_key: str = None, creation_time: Optional[int] = None,
                 kafka_key: Optional[str] = None, headers: Optional[Iterable[Tuple[Any, Any]]] = None,
                 masking_fields: Optional[Union[Dict[str, int], List[str]]] = None, headers_required: bool = True,
                 validators: Iterable[MessageValidator] = ()):
        self.logging_uuid = str(uuid.uuid4())
        self._value = value
        self.topic_key = topic_key
        self.kafka_key = kafka_key
        self.creation_time = creation_time or current_time_ms()
        self._headers_required = headers_required
        if self._headers_required and headers is None:
            raise LookupError(f"{self.__class__.__name__} no incoming headers.")
        self.headers = Headers(headers or {})
        self._callback_id = None  # FIXME: by some reason it possibly to change callback_id
        self.masking_fields = masking_fields
        self.validators = validators

    def validate(self) -> bool:
        """Try to json.load message and check for all required fields"""
        for validator in self.validators:
            if not validator.validate(self.message_name, self.payload):
                return False

        if self._headers_required and not self.headers:
            log("Message headers is empty", level="ERROR")
            return False

        try:
            message_name = self.as_dict.get(self.MESSAGE_NAME)
            required_fields = self._REQUIRED_FIELDS_MAP.get(message_name) or self._REQUIRED_FIELDS_MAP[None]
            for r_field in required_fields:
                if r_field not in self.as_dict:
                    self.print_validation_error(r_field)
                    return False

                if r_field not in self.__annotations__:
                    continue

                if not isinstance(
                        self.as_dict[r_field],
                        self.__annotations__[r_field],
                ):
                    self.print_validation_error(
                        r_field,
                        self.__annotations__[r_field],
                    )
                    return False

        except (json.JSONDecodeError, TypeError):
            log(
                "Message validation error: json decode error",
                exc_info=True,
                level="ERROR",
            )
            self.print_validation_error()
            return False

        return True

    def print_validation_error(
            self,
            required_field: Optional[str] = None,
            required_field_type: Optional[str] = None,
    ) -> None:
        if self._value:
            params = {
                "value": str(self._value),
                "required_field": required_field,
                "required_field_type": required_field_type,
                log_const.KEY_NAME: log_const.EXCEPTION_VALUE
            }
            if required_field and required_field_type:
                log(
                    "Message validation error: Expected '%(required_field)s'"
                    " of type '%(required_field_type)s': %(value)s",
                    params=params,
                    level="ERROR",
                )
            elif required_field:
                log(
                    "Message validation error: Required field "
                    "'%(required_field)s' is missing: %(value)s",
                    params=params,
                    level="ERROR",
                )
            else:
                log(
                    "Message validation error: Format is wrong: %(value)s",
                    params=params,
                    level="ERROR",
                )
        else:
            log("Message validation error: Message is empty", level="ERROR")

    @property
    def _callback_id_header_name(self) -> str:
        return CALLBACK_ID_HEADER

    @property
    def session_id(self) -> Optional[str]:
        return self.as_dict.get(self.SESSION_ID)

    # database user_id
    @property
    def db_uid(self) -> str:
        return "{}_{}".format(self.uid, self.channel)

    @property
    def channel(self) -> Optional[str]:
        return self.uuid.get(field.USER_CHANNEL)

    @channel.setter
    def channel(self, value):
        self.uuid[field.USER_CHANNEL] = value

    @property
    def uid(self) -> Optional[str]:
        return self.uuid.get(field.USER_ID)

    @property
    def sub(self) -> Optional[str]:
        return self.uuid.get(field.SUB)

    @property
    def uuid(self) -> Dict[str, str]:
        return self.as_dict[self.UUID]

    @property
    def payload(self) -> Dict[str, Any]:
        return self.as_dict[self.PAYLOAD]

    @payload.setter
    def payload(self, payload):
        self._value[self.PAYLOAD] = payload

    @property
    def type(self) -> str:
        return self.as_dict[self.MESSAGE_NAME]

    def project_name(self) -> Optional[str]:
        return self.payload.get(field.PROJECT_NAME)

    @property
    def intent(self) -> Optional[str]:
        return self.payload.get(field.INTENT)

    @property
    def device(self) -> Device:
        return Device(self.payload.get(field.DEVICE) or {})

    @property
    def app_info(self) -> AppInfo:
        return AppInfo(self.payload.get(field.APP_INFO) or {})

    @property
    def smart_bio(self) -> Dict[str, Any]:
        return self.payload.get(field.SMART_BIO) or {}

    @property
    def annotations(self) -> Dict[str, Dict[str, float]]:
        annotations = self.payload.get(field.ANNOTATIONS) or {}
        for annotation in annotations:
            classes = annotations[annotation][field.CLASSES]
            probas = annotations[annotation][field.PROBAS]
            annotations[annotation] = dict(zip(classes, probas))
        return annotations

    @property
    def callback_id(self) -> Optional[str]:
        if self._callback_id is not None:
            return self._callback_id

        try:
            from smart_kit.start_points.main_loop_http import HttpMainLoop
            if issubclass(get_app_config().MAIN_LOOP, HttpMainLoop):
                return str(self.incremental_id)
            return self.headers[self._callback_id_header_name]
        except KeyError:
            log(f"{self._callback_id_header_name} missed in headers for message_id %(message_id)s",
                params={log_const.KEY_NAME: "callback_id_missing", "message_id": self.incremental_id}, level="WARNING")
            return None

    @callback_id.setter
    def callback_id(self, value: str):
        self._callback_id = value

    @property
    def has_callback_id(self):
        return self._callback_id is not None or self.headers.get(self._callback_id_header_name) is not None

    # noinspection PyMethodMayBeStatic
    def generate_new_callback_id(self) -> str:
        from smart_kit.start_points.main_loop_http import HttpMainLoop
        if issubclass(get_app_config().MAIN_LOOP, HttpMainLoop):
            return str(self.incremental_id)
        return str(uuid.uuid4())

    @property
    def masked_value(self) -> str:
        masked_data = masking(self.as_dict, self.masking_fields)
        return json.dumps(masked_data, ensure_ascii=False)

    @property
    def message_name(self) -> str:
        return self.as_dict[self.MESSAGE_NAME]

    @message_name.setter
    def message_name(self, message_name: str):
        self._value[self.MESSAGE_NAME] = message_name

    # unique message_id
    @property
    def incremental_id(self) -> int:
        return self.as_dict[self.MESSAGE_ID]

    @property
    def as_dict(self) -> Dict[str, Any]:
        return self._value

    @property
    def as_str(self) -> str:
        return json.dumps(self._value, ensure_ascii=False)


basic_error_message = SmartAppFromMessage(
    {
        "messageName": "ERROR",
        "messageId": -1,
        "uuid": -1,
        "payload": {},
        "sessionId": -1
    },
    headers={},
    headers_required=False,
)

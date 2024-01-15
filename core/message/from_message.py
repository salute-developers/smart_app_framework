# coding=utf-8
from functools import cached_property
from typing import Iterable, Dict, Optional, Set, Any, List, Union, Tuple
import json
import uuid

from core.configs.global_constants import CALLBACK_ID_HEADER
from core.message.app_info import AppInfo
from core.message.device import Device
from core.message.message import SmartAppMessage
from core.names import field
import core.logging.logger_constants as log_const
from core.logging.logger_utils import log
from core.utils.masking_message import masking
from core.utils.utils import current_time_ms, mask_numbers
from core.message.validators.base_validator import BaseMessageValidator

from smart_kit.configs import get_app_config
from smart_kit.configs import settings


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


class SmartAppFromMessage(SmartAppMessage):
    MESSAGE_NAME = "messageName"
    MESSAGE_ID = "messageId"
    UUID = "uuid"
    PAYLOAD = "payload"
    SESSION_ID = "sessionId"
    CALLBACK_ID_HEADER_NAME = CALLBACK_ID_HEADER

    # following fields are used for validation
    incremental_id: int
    message_name: str
    payload: dict
    uuid: dict

    def __init__(self, value: Dict[str, Any], topic_key: str = None, creation_time: Optional[int] = None,
                 kafka_key: Optional[str] = None, headers: Optional[Iterable[Tuple[Any, Any]]] = None,
                 masking_fields: Optional[Union[Dict[str, int], List[str]]] = None, headers_required: bool = True,
                 validators: Iterable[BaseMessageValidator] = (), callback_id: Optional[str] = None):
        self.logging_uuid = str(uuid.uuid4())
        self._value = value
        self.topic_key = topic_key
        self.kafka_key = kafka_key
        self.creation_time = creation_time or current_time_ms()
        self._headers_required = headers_required
        if self._headers_required and headers is None:
            raise LookupError(f"{self.__class__.__name__} no incoming headers.")
        self.headers = Headers(headers or {})
        self._callback_id = callback_id  # FIXME: by some reason it possibly to change callback_id
        self.masking_fields = masking_fields
        self.validators = validators

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

    @cached_property
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
        mask_numbers_flag = settings.Settings()["template_settings"].get("mask_numbers", False)
        masked_data = mask_numbers(masking(self.as_dict, self.masking_fields)) if mask_numbers_flag else \
            masking(self.as_dict, self.masking_fields)
        return json.dumps(masked_data, ensure_ascii=False)

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

# coding: utf-8
from typing import Dict, Any


class Command:
    def __init__(self, name=None, params=None, action_id=None, request_type=None, request_data=None, loader=None,
                 need_payload_wrap=True, need_message_name=True):
        """
        Initialize Command instance with params

        :param name: str, command name
        :param params:
        :param action_id:
        :param request_type:
        :param request_data:
        :param loader: loader name for data before send. Possible loader values: orjson.dumps / protobuf
        """

        self.name: str = name
        self.payload: Dict[str, Any] = params or {}
        self.action_id: str = action_id
        self.request_type: str = request_type
        self.request_data: Dict[str, Any] = request_data or {}
        self.loader: str = loader or "orjson.dumps"
        self.need_payload_wrap: bool = need_payload_wrap
        self.need_message_name: bool = need_message_name

    @property
    def raw(self):
        message: Dict[str, Any] = {"payload": self.payload} if self.need_payload_wrap else self.payload
        if self.need_message_name:
            message["messageName"] = self.name
        return message

# coding: utf-8
import time
from copy import deepcopy
from typing import Dict, Any


class Command:
    def __init__(
        self,
        name=None,
        params=None,
        action_id=None,
        request_type=None,
        request_data=None,
        loader=None,
        need_payload_wrap=True,
        need_message_name=True,
        **kwargs
    ):
        """
        Initialize Command instance with params

        :param name: str, command name
        :param params:
        :param action_id:
        :param request_type:
        :param request_data:
        :param loader: loader name for data before send. Possible loader values: json.dumps / protobuf
        """

        self.name: str = name
        self.payload: Dict[str, Any] = params or {}
        self.action_id: str = action_id
        self.request_type: str = request_type
        self.request_data: Dict[str, Any] = request_data or {}
        self.loader: str = loader or "json.dumps"
        self.need_payload_wrap: bool = need_payload_wrap
        self.need_message_name: bool = need_message_name
        self.creation_time = time.time()

    @property
    def raw(self):
        message: Dict[str, Any] = {"payload": self.payload} if self.need_payload_wrap else self.payload
        if self.need_message_name:
            message["messageName"] = self.name
        return message

    @classmethod
    def from_command(
        cls,
        command: "Command",
        name=None,
        params=None,
        action_id=None,
        request_type=None,
        request_data=None,
        loader=None,
        need_payload_wrap=None,
        need_message_name=None,
    ) -> "Command":
        return cls(
            name=(name or command.name),
            params=(params or deepcopy(command.payload)),
            action_id=(action_id or command.action_id),
            request_type=(request_type or command.request_type),
            request_data=(request_data or deepcopy(command.request_data)),
            loader=(loader or command.loader),
            need_payload_wrap=(need_payload_wrap or command.need_payload_wrap),
            need_message_name=(need_message_name or command.need_message_name),
        )

# coding: utf-8


class Command:
    def __init__(self, name=None, params=None, action_id=None, request_type=None, request_data=None, loader=None,
                 need_payload_wrap=True):
        """
        Initialize Command instance with params

        :param name: str, command name
        :param params:
        :param action_id:
        :param request_type:
        :param request_data:
        :param loader: loader name for data before send. Possible loader values: json.dumps / protobuf
        """

        self.name = name
        self.payload = params or {}
        self.action_id = action_id
        self.request_type = request_type
        self.request_data = request_data or {}
        self.loader = loader or "json.dumps"
        self.need_payload_wrap = need_payload_wrap

    @property
    def raw(self):
        message = {"messageName": self.name, "action_id": self.action_id}
        message = {k: v for k, v in message.items() if v is not None}

        if self.need_payload_wrap:
            message["payload"] = self.payload
        else:
            message.update(self.payload)
        return message

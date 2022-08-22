# coding: utf-8
from typing import Union, Dict, List, Any, Optional

from core.basic_models.actions.command import Command
from core.basic_models.actions.string_actions import StringAction
from core.text_preprocessing.base import BaseTextPreprocessingResult
from core.utils.utils import deep_update_dict
from scenarios.user.user_model import User
from smart_kit.request.kafka_request import SmartKitKafkaRequest

PUSH_NOTIFY = "PUSH_NOTIFY"


class PushAction(StringAction):
    """ Action для отправки пуш уведомлений в сервис пушей.
        Example:
        {
          "push_advertising_offer": {
            "type": "push",
            "surface": "COMPANION", // не обязательное, по дефолту "COMPANION", без шаблонной генерации
            "content": {
                "notificationHeader": "{% if day_time = 'morning' %}Время завтракать!{% else %}Хотите что нибудь заказать?{% endif %}",
                "fullText": "В нашем магазине большой ассортимент{% if day_time = 'evening' %}. Успей заказать!{% endif %}",
                "mobileAppParameters": {
                    "DeeplinkAndroid": "{[ deep_link_url }}",
                    "DeeplinkIos": "{{ deep_link_url }}",
                    "Logo": "{{ icon_url }}"
                }
            }
          }
        }
    """
    DEFAULT_EXTRA_HEADERS = {
        "request-id": "{{ uuid4() }}",
        "sender-id": "{{ uuid4() }}",
        "simple": "true"
    }

    DEFAULT_REQUEST_DATA = {
        "topic_key": "push",
        "kafka_key": "main",
        SmartKitKafkaRequest.KAFKA_EXTRA_HEADERS: DEFAULT_EXTRA_HEADERS
    }

    COMPANION = "COMPANION"
    EX_HEADERS_NAME = SmartKitKafkaRequest.KAFKA_EXTRA_HEADERS

    def __init__(self, items: Dict[str, Any], id: Optional[str] = None):
        self.surface = items.get("surface", self.COMPANION)
        items["nodes"] = items.get("content") or {}
        items["command"] = PUSH_NOTIFY
        super().__init__(items, id)
        self.default_request_data_template = self._get_template_tree(self.DEFAULT_REQUEST_DATA)
        self.request_data_template = self._get_template_tree(self.request_data) if self.request_data else None

    def _render_request_data(self, action_params):
        request_data = self._get_rendered_tree_recursive(self.default_request_data_template, action_params)
        if self.request_data:
            request_data_update = self._get_rendered_tree_recursive(self.request_data_template, action_params)
            request_data = deep_update_dict(request_data, request_data_update)
        return request_data

    def run(self, user: User, text_preprocessing_result: BaseTextPreprocessingResult,
            params: Optional[Dict[str, Union[str, float, int]]] = None) -> List[Command]:
        params = params or {}
        command_params = {
            "projectId": user.settings["template_settings"]["project_id"],
            "clientId": user.message.sub,
            "surface": self.surface,
            "content": self._generate_command_context(user, text_preprocessing_result, params),
        }
        requests_data = self._render_request_data(params)
        commands = [Command(self.command, command_params, self.id, request_type=self.request_type,
                            request_data=requests_data, need_payload_wrap=False, need_message_name=False)]
        return commands

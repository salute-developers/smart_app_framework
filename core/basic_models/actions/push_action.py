# coding: utf-8
from copy import copy
from typing import Union, Dict, List, Any, Optional

from core.basic_models.actions.command import Command
from core.basic_models.actions.string_actions import StringAction
from core.text_preprocessing.base import BaseTextPreprocessingResult
from core.unified_template.unified_template import UnifiedTemplate
from core.utils.pickle_copy import pickle_deepcopy
from scenarios.user.user_model import User
from smart_kit.request.kafka_request import SmartKitKafkaRequest


class PushAction(StringAction):
    """
        Action для отправки пуш уведомлений в сервис пушей.
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
        super().__init__(items, id)

    def _render_request_data(self, action_params):
        # копируем прежде чем рендерить шаблон хэдеров, чтобы не затереть его
        if self.request_data:
            request_data = pickle_deepcopy(self.DEFAULT_REQUEST_DATA)
            request_data.update(self.request_data)
        else:
            request_data = self.DEFAULT_REQUEST_DATA
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
                            request_data=requests_data, payload_container=False)]
        return commands


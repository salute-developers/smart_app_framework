# coding: utf-8
import base64
import uuid
from typing import Union, Dict, List, Any, Optional

from core.basic_models.actions.command import Command
from core.basic_models.actions.string_actions import StringAction
from core.text_preprocessing.base import BaseTextPreprocessingResult
from core.utils.utils import deep_update_dict
from scenarios.user.user_model import User
from smart_kit.request.kafka_request import SmartKitKafkaRequest
from smart_kit.action.http import HTTPRequestAction

COMMON_BEHAVIOR = "common_behavior"
PUSH_NOTIFY = "PUSH_NOTIFY"


class PushAction(StringAction):
    """ Action для отправки пуш уведомлений в сервис пушей через Kafka.
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


class PushAuthenticationActionHttp(PushAction):
    """ Action для получения токена для вызова SmartPush API через http.

    Ссылка на документацию с примерами получения токена:
    - Аутентификация (получение токена): https://developers.sber.ru/docs/ru/va/how-to/app-support/smartpush/access

    Response:
        Результат запроса сохраняется в переменной user.variables, после выполнения метода process_result класса HTTPRequestAction.
        Для доступа к данным можно воспользоваться одним из следущих вариантов:
            - user.variables.raw or user.variables.raw["push_authentification_response"]
            - user.variables.value or user.variables.value["push_authentification_response"]

    Example:
        {
            "type": "push_authentication", // обязательный параметр
            "url": "some_url", // опциональный параметр, по дефолту https://salute.online.sberbank.ru:9443/api/v2/oauth
            "client_id": "@!89FB.4D62.3A51.A9EB!0001!96E5.AE89!0008!B1AF.DB7D.1586.84F3", // обязательный параметр
            "surface": "COMPANION", // опциональный параметр, по дефолту "COMPANION", без шаблонной генерации
            "client_secret": "secret", // обязательный параметр
            "behavior": "some_behavior" // опциональный параметр
        }
    """

    BASIC_METHOD_AUTH = "Basic "
    URL_OAUTH = "https://salute.online.sberbank.ru:9443/api/v2/oauth"

    def __init__(self, items: Dict[str, Any], id: Optional[str] = None):
        super().__init__(items, id)
        items["store"] = "push_authentification_response"
        items["behavior"] = items.get("behavior") or COMMON_BEHAVIOR
        items["params"] = {"url": items.get("url") or self.URL_OAUTH, "json": {"scope": "SMART_PUSH"}}
        items["params"]["headers"] = {}
        self.headers = items["params"]["headers"]
        self.headers["RqUID"] = str(uuid.uuid4())
        self.headers["Authorization"] = self._create_authorization_token(items)
        self.headers["Content-Type"] = "application/x-www-form-urlencoded"
        self._create_instance_of_http_request_action(items, id)

    def _create_instance_of_http_request_action(self, items: Dict[str, Any], id: Optional[str] = None):
        self.http_request_action = HTTPRequestAction(items, id)

    def _create_authorization_token(self, items: Dict[str, Any]) -> str:
        client_id = items["client_id"]
        client_secret = items["client_secret"]
        auth_string = base64.b64encode((client_id + ":" + client_secret).encode("ascii"))
        authorization_token = self.BASIC_METHOD_AUTH + auth_string.decode("ascii")
        return authorization_token

    def run(self, user: User, text_preprocessing_result: BaseTextPreprocessingResult,
            params: Optional[Dict[str, Union[str, float, int]]] = None) -> List[Command]:
        params = params or {}
        collected = user.parametrizer.collect(text_preprocessing_result, filter_params={"command": self.command})
        params.update(collected)
        self.http_request_action.run(user, text_preprocessing_result, params)
        return []


class PushActionHttp(PushAction):
    """ Action для отправки пуш уведомлений в SmartPush API через http.

    Аутентификация:
     - Осуществляется с помощью access_token, который можно получить через PushAuthenticationActionHttp
    Ссылка на документацию с примерами отправки уведомлений:
     - Отправка уведомлений: https://developers.sber.ru/docs/ru/va/how-to/app-support/smartpush/api/sending-notifications

    Response:
        Результат запроса сохраняется в переменной user.variables, после выполнения метода process_result класса HTTPRequestAction.
        Для доступа к данным можно воспользоваться одним из следущих вариантов:
            - user.variables.raw or user.variables.raw["push_http_response"]
            - user.variables.value or user.variables.value["push_http_response"]

    Example Basic Request ("type_request": "apprequest-lite"):
        {
            "type": "push_http", // обязательный параметр
            "type_request": "apprequest-lite", // обязательный параметр
            "behavior": "some_behavior", // опциональный параметр
            "surface": "COMPANION", // опциональный параметр, по дефолту "COMPANION", без шаблонной генерации
            "url": "some_url", // опциональный параметр, по дефолту https://salute.online.sberbank.ru:9443/api/v2/smartpush/apprequest-lite
            "access_token": "eyJlbmMiOiJBMjU2Q0JDLUhTNTEyIiwiYWxnIjoiUVAtMjU2In0", // обязательный параметр (получить можно через PushAuthenticationActionHttp)
            "callbackUrl": "some_url", // опциональный параметр headers (URL для доставки статусов уведомлений)
            "templateContent": { // обязательный параметр (Параметры шаблона)
                "id": "49061553-27c7-4471-9145-d8d6137657da", // обязательный параметр (Идентификатор шаблона)
                "headerValues": { // опциональный параметр (Набор значений переменных заголовка из шаблона)
                    "clientname": "Иван", // Произвольная переменная из заголовка шаблона
                    "bandname": "Ласковый май" // Произвольная переменная из заголовка шаблона
                },
                "bodyValues": { // опциональный параметр (Набор значений переменных текста из шаблона)
                    "formatname": "альбома", // Произвольная переменная из текста шаблона
                    "bandname": "Ласковый май", // Произвольная переменная из текста шаблона
                    "releasename": "Новое" // Произвольная переменная из текста шаблона
                }
            }
        }

    Example Advanced Request ("type_request": "apprequest"):
        {
            "type": "push_http", // обязательный параметр
            "type_request": "apprequest", // обязательный параметр
            "behavior": "some_behavior", // опциональный параметр
            "access_token": "eyJlbmMiOiJBMjU2Q0JDLUhTNTEyIiwiYWxnIjoiUVAtMjU2In0", // обязательный параметр (получить можно через PushAuthenticationActionHttp)
            "url": "some_url", // опциональный параметр, по дефолту https://salute.online.sberbank.ru:9443/api/v2/smartpush/apprequest
            "protocolVersion": "V1", // обязательный параметр (Формат протокола)
            "messageId": 37284759, // обязательный параметр (Идентификатор клиентского сообщения в рамках сессии)
            "messageName": "SEND_PUSH", // опциональный параметр (Тип сообщения)
            "callbackUrl": "some_url", // опциональный параметр headers (URL для доставки статусов уведомлений)
            "senderApplication": { // опциональный параметр (Информация о приложении)
              "appId": "3fa85f64-5717-4562-b3fc-2c963f66afa7", // обязательный параметр (Идентификатор смартапа)
              "versionId": "fcac2f61-57a7-4d6d-b3fc-2c963f66a111" // обязательный параметр (Идентификатор версии смартапа)
            },
            "deliveryMode": "broadcast", // обязательный параметр (Тип доставки. Возможные значения: broadcast, sequential)
            "destinations": [
                {
                  "channel": "COMPANION_B2C", // обязательный параметр (Канал получателя)
                  "surface": "COMPANION", // обязательный параметр (Поверхность получателя)
                  "templateContent": { // обязательный параметр (Содержимое настроек для получателя под текущим номером)
                    "id": "49061553-27c7-4471-9145-d8d6137657da", // обязательный параметр (Идентификатор шаблона)
                    "headerValues": { // опциональный параметр (Набор значений переменных заголовка из шаблона)
                        "clientname": "Иван", // Произвольная переменная из заголовка шаблона
                        "bandname": "Ласковый май" // Произвольная переменная из заголовка шаблона
                    },
                    "bodyValues": { // опциональный параметр (Набор значений переменных текста из шаблона)
                        "formatname": "альбома", // Произвольная переменная из текста шаблона
                        "bandname": "Ласковый май", // Произвольная переменная из текста шаблона
                        "releasename": "Новое" // Произвольная переменная из текста шаблона
                    }
                    "mobileAppParameters": { // опциональный параметр (Блок с параметрами для отправки в мобильное приложение Салют)
                      "deeplinkAndroid": "laskoviyi-mai-listen-android", // опциональный параметр (Сценарий для Android-устройств)
                      "deeplinkIos": "laskoviyi-mai-listen-ios" // опциональный параметр (Сценарий для iOS-устройств)
                    },
                    "timeFrame": { // опциональный параметр (Настройки времени для отложенной отправки push-уведомления под текущим номером)
                      "startTime": "13:30:00", // обязательный параметр (Стартовое время отправки push-уведомления)
                      "finishTime": "15:00:00", // обязательный параметр (Финальное время отправки push-уведомления)
                      "timeZone": "GMT+03:00", // обязательный параметр (Часовой пояс пользователя в формате GMT+hh:mm)
                      "startDate": "2020-06-04", // обязательный параметр (Стартовая дата отправки push-уведомления)
                      "endDate": "2020-06-05" // опциональный параметр (Финальная дата отправки push-уведомления)
                    }
                  }
                }
            ]
        }
    """

    BEARER_METHOD_AUTH = "Bearer "
    URL_OAUTH_APPREQUEST_LITE = "https://salute.online.sberbank.ru:9443/api/v2/smartpush/apprequest-lite"
    URL_OAUTH_APPREQUEST = "https://salute.online.sberbank.ru:9443/api/v2/smartpush/apprequest"
    CLIENT_ID_TYPE = "SUB"

    def __init__(self, items: Dict[str, Any], id: Optional[str] = None):
        super().__init__(items, id)

        self.type_request = items.get("type_request")
        if self.type_request == "apprequest-lite":
            self.templateContent = items.get("templateContent")
            items["params"] = {"url": items.get("url") or self.URL_OAUTH_APPREQUEST_LITE}
        elif self.type_request == "apprequest":
            items["payload"] = {}
            self.payload = items["payload"]
            self.sender = self.payload["sender"] = {}
            self.recipient = self.payload["recipient"] = {}
            self.clientId = self.recipient["clientId"] = {}
            self.deliveryConfig = self.payload["deliveryConfig"] = {}

            self.sender["application"] = items.get("senderApplication")
            self.clientId["idType"] = self.CLIENT_ID_TYPE
            self.deliveryConfig["deliveryMode"] = items["deliveryMode"]
            self.deliveryConfig["destinations"] = items["destinations"]

            items["params"] = {"url": items.get("url") or self.URL_OAUTH_APPREQUEST}
            self.protocolVersion = items["protocolVersion"]
            self.messageId = items["messageId"]
            self.messageName = items.get("messageName")

        items["store"] = "push_http_response"
        items["behavior"] = items.get("behavior") or COMMON_BEHAVIOR
        items["params"]["headers"] = {}
        self.headers = items["params"]["headers"]
        self.headers["RqUID"] = str(uuid.uuid4())
        self.headers["Authorization"] = self.BEARER_METHOD_AUTH + items["access_token"]
        self.headers["Content-Type"] = "application/json"
        self.headers["callbackUrl"] = items.get("callbackUrl")
        self._create_instance_of_http_request_action(items, id)

    def _create_instance_of_http_request_action(self, items: Dict[str, Any], id: Optional[str] = None):
        self.http_request_action = HTTPRequestAction(items, id)

    def run(self, user: User, text_preprocessing_result: BaseTextPreprocessingResult,
            params: Optional[Dict[str, Union[str, float, int]]] = None) -> List[Command]:
        params = params or {}
        collected = user.parametrizer.collect(text_preprocessing_result, filter_params={"command": self.command})
        params.update(collected)
        if self.type_request == "apprequest-lite":
            request_body_parameters = {
                "projectId": user.settings["template_settings"]["project_id"],
                "clientId": user.message.sub,
                "surface": self.surface,
                "templateContent": self.templateContent
            }
        elif self.type_request == "apprequest":
            self.sender["projectId"] = user.settings["template_settings"]["project_id"]
            self.clientId["id"] = user.message.sub
            request_body_parameters = {
                "protocolVersion": self.protocolVersion,
                "messageId": self.messageId,
                "messageName": self.messageName,
                "payload": {
                    "sender": self.sender,
                    "recipient": self.recipient,
                    "deliveryConfig": self.deliveryConfig
                }
            }
        self.http_request_action.method_params["json"] = request_body_parameters
        self.http_request_action.run(user, text_preprocessing_result, params)
        return []

# coding: utf-8
import base64
import uuid
from typing import Union, Dict, List, Any, Optional

from core.basic_models.actions.command import Command
from core.basic_models.actions.string_actions import StringAction
from core.text_preprocessing.base import BaseTextPreprocessingResult
from core.utils.pickle_copy import pickle_deepcopy
from core.utils.utils import deep_update_dict
from scenarios.user.user_model import User
from smart_kit.request.kafka_request import SmartKitKafkaRequest
from smart_kit.action.http import HTTPRequestAction

COMMON_BEHAVIOR = "common_behavior"
PUSH_NOTIFY = "PUSH_NOTIFY"
GET_RUNTIME_PERMISSIONS = "GET_RUNTIME_PERMISSIONS"


class PushAction(StringAction):
    """ Action для отправки пуш уведомлений в сервис пушей через Kafka.
        Example:
        {
          "push_advertising_offer": {
            "type": "push",
            "surface": "COMPANION", // не обязательное, по дефолту "COMPANION", без шаблонной генерации
            "content": {
                "notificationHeader": "{% if day_time = 'morning' %}Время завтракать!"
                                      "{% else %}Хотите что нибудь заказать?{% endif %}",
                "fullText": "В нашем магазине большой ассортимент"
                            "{% if day_time = 'evening' %}. Успей заказать!{% endif %}",
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
    Шаблонная генерация:
     - Для всех полей доступна шаблонная генерация. Можно также передавать значение обычной строкой.

    Response:
        Результат запроса сохраняется в переменной user.variables, после выполнения метода process_result класса HTTPRequestAction.  # noqa
        Для доступа к данным можно воспользоваться одним из следущих вариантов:
            - user.variables.raw or user.variables.raw["push_authentification_response"]
            - user.variables.value or user.variables.value["push_authentification_response"]

    Example:
        {
            "type": "push_authentication", // обязательный параметр
            "url": "some_url", // опциональный параметр, по дефолту https://salute.online.sberbank.ru:9443/api/v2/oauth
            "client_id": "@!89FB.4D62.3A51.A9EB!0001!96E5.AE89!0008!B1AF.DB7D.1586.84F3", // обязательный параметр
            "client_secret": "secret", // обязательный параметр
            "behavior": "some_behavior" // опциональный параметр, по дефолту "common_behavior"
        }
    """

    BASIC_METHOD_AUTH = "Basic "
    URL_OAUTH = "https://salute.online.sberbank.ru:9443/api/v2/oauth"

    def __init__(self, items: Dict[str, Any], id: Optional[str] = None):
        super().__init__(items, id)
        items["store"] = "push_authentification_response"
        items["behavior"] = items.get("behavior") or COMMON_BEHAVIOR
        items["params"] = {"url": items.get("url") or self.URL_OAUTH, "data": "scope=SMART_PUSH".encode()}
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
        return self.http_request_action.run(user, text_preprocessing_result, params)


class GetRuntimePermissionsAction(PushAction):
    """ Action для получения разрешения на отправку пуш уведомлений в SmartPush API через http.

    Ссылка на документацию с примерами получения разрешения на уведомления:
     - Разрешение на уведомления: https://developers.sber.ru/docs/ru/va/how-to/app-support/smartpush/api/permission-notifications  # noqa

    Note: Навык на HTTP не поддерживает использование двух команд на один сценарий, поэтому в success_action'е
          behavior'а необходимо прописать продолжение сценария с использованием PushActionHttp.

    Response (Error codes):
        - 001 (SUCCESS): Данные существуют и получено клиентское согласие;
        - 101 (CLIENT DENIED): Клиент отклонил разрешение;
        - 102 (FORBIDDEN): Запрещенный вызов от смартапа для GET_RUNTIME_PERMISSIONS.

    Example:
        {
            "type": "get_runtime_permissions", // обязательный параметр
            "behavior": "common_behavior" // обязательный параметр.
        }
    """

    def __init__(self, items: Dict[str, Any], id: Optional[str] = None):
        super().__init__(items, id)
        self.behavior = items.get("behavior") or COMMON_BEHAVIOR
        self.command = GET_RUNTIME_PERMISSIONS

    def run(self, user: User, text_preprocessing_result: BaseTextPreprocessingResult,
            params: Optional[Dict[str, Union[str, float, int]]] = None) -> List[Command]:
        params = params or {}
        scenario_id = user.last_scenarios.last_scenario_name
        user.behaviors.add(user.message.generate_new_callback_id(), self.behavior, scenario_id,
                           text_preprocessing_result.raw, action_params=pickle_deepcopy(params))
        self.nodes = {
            "messageName": GET_RUNTIME_PERMISSIONS,
            "server_action": {
                "parameters": {
                    "need_actions": {
                        "types": ["service_push"]
                    }
                }
            }
        }
        command_params = self._generate_command_context(user, text_preprocessing_result, params)
        commands = [Command(self.command, command_params, self.id, request_type=self.request_type,
                            request_data=self.request_data, need_payload_wrap=False, need_message_name=False)]
        return commands


class PushActionHttp(PushAction):
    """ Action для отправки пуш уведомлений в SmartPush API через http.

    Аутентификация:
     - Осуществляется с помощью access_token, который можно получить через PushAuthenticationActionHttp
    Ссылка на документацию с примерами отправки уведомлений:
     - Отправка уведомлений: https://developers.sber.ru/docs/ru/va/how-to/app-support/smartpush/api/sending-notifications  # noqa
    Шаблонная генерация:
     - Для всех полей доступна шаблонная генерация. Можно также передавать значение обычной строкой.

    Response:
        Результат запроса сохраняется в переменной user.variables, после выполнения метода process_result класса HTTPRequestAction.  # noqa
        Для доступа к данным можно воспользоваться одним из следущих вариантов:
            - user.variables.raw or user.variables.raw["push_http_response"]
            - user.variables.value or user.variables.value["push_http_response"]

    Example Basic Request ("type_request": "apprequest-lite"):
        {
            "type": "push_http", // обязательный параметр
            "type_request": "apprequest-lite", // обязательный параметр
            "behavior": "some_behavior", // опциональный параметр, по дефолту "common_behavior"
            "surface": "COMPANION", // обязательный параметр.
            "url": "some_url", // опциональный параметр, по дефолту https://salute.online.sberbank.ru:9443/api/v2/smartpush/apprequest-lite  # noqa
            "access_token": "{{variables.push_authentification_response.access_token}}", // обязательный параметр (получить можно через PushAuthenticationActionHttp)  # noqa
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
            "behavior": "some_behavior", // опциональный параметр, по дефолту "common_behavior"
            "access_token": "{{variables.push_authentification_response.access_token}}", // обязательный параметр (получить можно через PushAuthenticationActionHttp)  # noqa
            "url": "some_url", // опциональный параметр, по дефолту https://salute.online.sberbank.ru:9443/api/v2/smartpush/apprequest
            "callbackUrl": "some_url", // опциональный параметр headers (URL для доставки статусов уведомлений)
            "sender": {
                "projectId": "3fa85f64-5717-4562-b3ab-2c963f66baa6"
            },
            "deliveryConfig": {
                "deliveryMode": "broadcast", // обязательный параметр (Тип доставки. Возможные значения: broadcast, sequential)
                "destinations": [
                    {
                        "channel": "COMPANION_B2C", // обязательный параметр (Канал получателя).
                        "surface": "COMPANION", // обязательный параметр (Поверхность получателя).
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
        }
    """

    BEARER_METHOD_AUTH = "Bearer "
    URL_OAUTH_APPREQUEST_LITE = "https://salute.online.sberbank.ru:9443/api/v2/smartpush/apprequest-lite"
    URL_OAUTH_APPREQUEST = "https://salute.online.sberbank.ru:9443/api/v2/smartpush/apprequest"

    def __init__(self, items: Dict[str, Any], id: Optional[str] = None):
        super().__init__(items, id)
        self.type_request = items["type_request"]

        if self.type_request == "apprequest-lite":
            self.surface = items["surface"]
            self.templateContent = items["templateContent"]
            items["params"] = {"url": items.get("url") or self.URL_OAUTH_APPREQUEST_LITE}
        elif self.type_request == "apprequest":
            items["payload"] = {}
            self.payload = items["payload"]
            self.payload["sender"] = items["sender"]
            self.payload["sender"]["application"] = {"appId": None, "versionId": None}
            self.payload["recipient"] = items["recipient"]
            self.payload["deliveryConfig"] = items["deliveryConfig"]
            items["params"] = {"url": items.get("url") or self.URL_OAUTH_APPREQUEST}
        else:
            raise Exception("Invalid items[type_request]")

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
                "projectId": user.message.app_info.project_id,
                "clientId": user.message.sub,
                "surface": self.surface,
                "templateContent": self.templateContent
            }
        elif self.type_request == "apprequest":
            self.payload["sender"]["application"]["appId"] = user.message.app_info.application_id
            self.payload["sender"]["application"]["versionId"] = user.message.app_info.app_version_id
            request_body_parameters = {
                "protocolVersion": "V1",
                "messageId": user.message.incremental_id,
                "messageName": "SEND_PUSH",
                "payload": self.payload
            }
        self.http_request_action.method_params["json"] = request_body_parameters
        return self.http_request_action.run(user, text_preprocessing_result, params)

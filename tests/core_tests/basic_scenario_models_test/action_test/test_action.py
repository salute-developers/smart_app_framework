# coding: utf-8
import json
import unittest
import uuid
from unittest.mock import Mock, MagicMock, patch

from core.basic_models.actions.basic_actions import Action, DoingNothingAction, action_factory, RequirementAction, \
    actions, ChoiceAction, ElseAction, CompositeAction, NonRepeatingAction
from core.basic_models.actions.client_profile_actions import GiveMeMemoryAction, RememberThisAction
from core.basic_models.actions.command import Command
from core.basic_models.actions.counter_actions import CounterIncrementAction, CounterDecrementAction, \
    CounterClearAction, CounterSetAction, CounterCopyAction
from core.basic_models.actions.external_actions import ExternalAction
from core.basic_models.actions.push_action import PushAction, PushAuthenticationActionHttp, PushActionHttp, \
    GetRuntimePermissionsAction
from core.basic_models.actions.string_actions import StringAction, AfinaAnswerAction, SDKAnswer, \
    SDKAnswerToUser, NodeAction
from core.basic_models.answer_items.answer_items import SdkAnswerItem, items_factory, answer_items, BubbleText, \
    ItemCard, PronounceText, SuggestText, SuggestDeepLink
from core.basic_models.requirement.basic_requirements import requirement_factory, Requirement, requirements
from core.model.registered import registered_factories
from core.text_preprocessing.base import BaseTextPreprocessingResult
from core.unified_template.unified_template import UnifiedTemplate, UNIFIED_TEMPLATE_TYPE_NAME
from smart_kit.action.http import HTTPRequestAction
from smart_kit.request.kafka_request import SmartKitKafkaRequest
from smart_kit.utils.picklable_mock import PicklableMock, PicklableMagicMock


class MockParametrizer:
    def __init__(self, user, items=None):
        self.items = items or {}
        self.user = user
        self.data = items.get("data") or {}
        self.filter = items.get("filter") or False

    def collect(self, text_preprocessing_result=None, filter_params=None):
        data = {
            "payload": self.user.message.payload
        }
        data.update(self.data)
        if self.filter:
            data.update({"filter": "filter_out"})
        return data


class MockAction:
    def __init__(self, items=None):
        items = items or {}
        self.result = items.get("result")

    def run(self, user, text_preprocessing_result, params=None):
        return self.result or ["test action run"]


class UserMockAction:
    def __init__(self, items=None):
        items = items or {}
        self.result = items.get("result")
        self.done = False

    def run(self, user, text_preprocessing_result, params=None):
        self.done = True


class MockRequirement:
    def __init__(self, items):
        self.result = items.get("result")

    def check(self, text_preprocessing_result, user, params):
        return self.result


class MockSimpleParametrizer:
    def __init__(self, user, items=None):
        self.user = user
        self.data = items.get("data")

    def collect(self, text_preprocessing_result, filter_params=None):
        return self.data


class ActionTest(unittest.TestCase):
    def test_nodes_1(self):
        items = {"nodes": {"answer": "test"}}
        action = NodeAction(items)
        nodes = action.nodes
        action_key = list(nodes.keys())[0]
        self.assertEqual(action_key, 'answer')
        self.assertIsInstance(nodes[action_key], UnifiedTemplate)

    def test_nodes_2(self):
        items = {}
        action = NodeAction(items)
        nodes = action.nodes
        self.assertEqual(nodes, {})

    def test_base(self):
        items = {"nodes": "test"}
        action = Action(items)
        result = action.run(None, None)
        self.assertEqual(result, [])

    def test_external(self):
        items = {"action": "test_action_key"}
        action = ExternalAction(items)
        user = PicklableMock()
        user.descriptions = {"external_actions": {"test_action_key": MockAction()}}
        self.assertEqual(action.run(user, None), ["test action run"])

    def test_doing_nothing_action(self):
        items = {"nodes": {"answer": "test"}, "command": "test_name"}
        action = DoingNothingAction(items)
        result = action.run(None, None)
        self.assertIsInstance(result, list)
        command = result[0]
        self.assertIsInstance(command, Command)
        self.assertEqual(command.name, "test_name")
        self.assertEqual(command.payload, {"answer": "test"})

    def test_requirement_action(self):
        registered_factories[Requirement] = requirement_factory
        requirements["test"] = MockRequirement
        registered_factories[Action] = action_factory
        actions["test"] = MockAction
        items = {"requirement": {"type": "test", "result": True}, "action": {"type": "test"}}
        action = RequirementAction(items)
        self.assertIsInstance(action.requirement, MockRequirement)
        self.assertIsInstance(action.internal_item, MockAction)
        self.assertEqual(action.run(None, None), ["test action run"])
        items = {"requirement": {"type": "test", "result": False}, "action": {"type": "test"}}
        action = RequirementAction(items)
        result = action.run(None, None)
        self.assertEqual([], result)

    def test_requirement_choice(self):
        items = {"requirement_actions": [
            {"requirement": {"type": "test", "result": False}, "action": {"type": "test", "result": ["action1"]}},
            {"requirement": {"type": "test", "result": True}, "action": {"type": "test", "result": ["action2"]}}
        ]}
        choice_action = ChoiceAction(items)
        self.assertIsInstance(choice_action.items, list)
        self.assertIsInstance(choice_action.items[0], RequirementAction)
        result = choice_action.run(None, None)
        self.assertEqual(result, ["action2"])

    def test_requirement_choice_else(self):
        items = {
            "requirement_actions": [
                {"requirement": {"type": "test", "result": False}, "action": {"type": "test", "result": "action1"}},
                {"requirement": {"type": "test", "result": False}, "action": {"type": "test", "result": "action2"}},
            ],
            "else_action": {"type": "test", "result": ["action3"]}
        }
        choice_action = ChoiceAction(items)
        self.assertIsInstance(choice_action.items, list)
        self.assertIsInstance(choice_action.items[0], RequirementAction)
        result = choice_action.run(None, None)
        self.assertEqual(result, ["action3"])

    def test_string_action(self):
        expected = [Command("cmd_id", {"item": "template", "params": "params"})]
        user = PicklableMagicMock()
        template = PicklableMock()
        template.get_template = Mock(return_value=["nlpp.payload.personInfo.identityCard"])
        user.descriptions = {"render_templates": template}
        params = {"params": "params"}
        user.parametrizer = MockSimpleParametrizer(user, {"data": params})
        items = {"command": "cmd_id",
                 "nodes":
                     {"item": "template", "params": "{{params}}"}}
        action = StringAction(items)
        result = action.run(user, None)
        self.assertEqual(expected[0].name, result[0].name)
        self.assertEqual(expected[0].payload, result[0].payload)

    def test_else_action_if(self):
        registered_factories[Requirement] = requirement_factory
        requirements["test"] = MockRequirement
        registered_factories[Action] = action_factory
        actions["test"] = MockAction
        user = PicklableMock()
        items = {
            "requirement": {"type": "test", "result": True},
            "action": {"type": "test", "result": ["main_action"]},
            "else_action": {"type": "test", "result": ["else_action"]}
        }
        action = ElseAction(items)
        self.assertEqual(action.run(user, None), ["main_action"])

    def test_else_action_else(self):
        registered_factories[Requirement] = requirement_factory
        requirements["test"] = MockRequirement
        registered_factories[Action] = action_factory
        actions["test"] = MockAction
        user = PicklableMock()
        items = {
            "requirement": {"type": "test", "result": False},
            "action": {"type": "test", "result": ["main_action"]},
            "else_action": {"type": "test", "result": ["else_action"]}
        }
        action = ElseAction(items)
        self.assertEqual(action.run(user, None), ["else_action"])

    def test_else_action_no_else_if(self):
        registered_factories[Requirement] = requirement_factory
        requirements["test"] = MockRequirement
        registered_factories[Action] = action_factory
        actions["test"] = MockAction
        user = PicklableMock()
        items = {
            "requirement": {"type": "test", "result": True},
            "action": {"type": "test", "result": ["main_action"]},
        }
        action = ElseAction(items)
        self.assertEqual(action.run(user, None), ["main_action"])

    def test_else_action_no_else_else(self):
        registered_factories[Requirement] = requirement_factory
        requirements["test"] = MockRequirement
        registered_factories[Action] = action_factory
        actions["test"] = MockAction
        user = PicklableMock()
        items = {
            "requirement": {"type": "test", "result": False},
            "action": {"type": "test", "result": ["main_action"]},
        }
        action = ElseAction(items)
        result = action.run(user, None)
        self.assertEqual([], result)

    def test_composite_action(self):
        registered_factories[Action] = action_factory
        actions["action_mock"] = MockAction
        user = PicklableMock()
        items = {
            "actions": [
                {"type": "action_mock"},
                {"type": "action_mock"}
            ]
        }
        action = CompositeAction(items)
        result = action.run(user, None)
        self.assertEqual(['test action run', 'test action run'], result)

    def test_node_action_support_templates(self):
        params = {
            "markup": "italic",
            "email": "heyho@sberbank.ru",
            "name": "Buratino"
        }
        items = {
            "support_templates": {
                "markup": "{%if markup=='italic'%}i{% else %}b{% endif %}",
                "email": "{%if email%}<{{markup}}>Email: {{email}}</{{markup}}>\n{% endif %}",
                "name": "{%if name%}<{{markup}}>Name: {{name}}</{{markup}}>\n{% endif %}",
                "result": "{{email}}{{name}}"
            },
            "nodes": {
                "answer": "{{result|trim}}"
            }
        }
        expected = "<i>Email: heyho@sberbank.ru</i>\n<i>Name: Buratino</i>"

        action = StringAction(items)
        for template_key, template in action.support_templates.items():
            self.assertIsInstance(template, UnifiedTemplate)
        user = PicklableMagicMock()
        user.parametrizer = MockSimpleParametrizer(user, {"data": params})
        output = action.run(user=user, text_preprocessing_result=None)[0].payload["answer"]
        self.assertEqual(output, expected)

    def test_string_action_support_templates(self):
        params = {
            "answer_text": "some_text",
            "buttons_number": 3
        }
        items = {
            "nodes": {
                "answer": "{{ answer_text }}",
                "buttons": {
                    "type": UNIFIED_TEMPLATE_TYPE_NAME,
                    "template": "{{range(buttons_number)|list}}",
                    "loader": "json"
                }
            }
        }
        expected = {
            "answer": "some_text",
            "buttons": [0, 1, 2]
        }
        action = StringAction(items)
        user = PicklableMagicMock()
        user.parametrizer = MockSimpleParametrizer(user, {"data": params})
        output = action.run(user=user, text_preprocessing_result=None)[0].payload
        self.assertEqual(output, expected)

    def test_push_action(self):
        params = {
            "day_time": "morning",
            "deep_link_url": "some_url",
            "icon_url": "some_icon_url"
        }
        settings = {"template_settings": {"project_id": "project_id"}}
        items = {
            "request_data": {
                "kafka_extraHeaders": {
                    "request-id": "{{ 1 }}"
                }
            },
            "content": {
                "notificationHeader": "{% if day_time == 'morning' %}Время завтракать!{% else %}Хотите что нибудь заказать?{% endif %}",
                "fullText": "В нашем магазине большой ассортимент{% if day_time == 'evening' %}. Успей заказать!{% endif %}",
                "mobileAppParameters": {
                    "DeeplinkAndroid": "{{ deep_link_url }}",
                    "DeeplinkIos": "{{ deep_link_url }}",
                    "Logo": "{{ icon_url }}"
                }
            }
        }
        user = PicklableMagicMock()

        expected = {
            "surface": "COMPANION",
            "projectId": "project_id",
            "clientId": user.message.sub,
            "content": {
                "notificationHeader": "Время завтракать!",
                "fullText": "В нашем магазине большой ассортимент",
                "mobileAppParameters": {
                    "DeeplinkAndroid": "some_url",
                    "DeeplinkIos": "some_url",
                    "Logo": "some_icon_url"
                }
            }
        }
        action = PushAction(items)
        user.parametrizer = MockSimpleParametrizer(user, {"data": params})
        user.settings = settings
        command = action.run(user=user, text_preprocessing_result=None)[0]
        self.assertEqual(command.raw, expected)
        # проверяем наличие кастомных хэдеров для сервиса пушей
        self.assertTrue(SmartKitKafkaRequest.KAFKA_EXTRA_HEADERS in command.request_data)
        headers = command.request_data.get(SmartKitKafkaRequest.KAFKA_EXTRA_HEADERS)
        self.assertTrue('request-id' in headers)
        self.assertTrue('sender-id' in headers)
        self.assertEqual(headers.get('request-id'), "1")
        self.assertTrue(uuid.UUID(headers.get('sender-id'), version=3))

    def test_push_authentication_action_http(self):
        items = {
            "type": "push_authentication",
            "client_id": "@!89FB.4D62.3A51.A9EB!0001!96E5.AE89!0008!B1AF.DB7D.1586.84F3",
            "surface": "COMPANION",
            "client_secret": "secret"
        }

        action = PushAuthenticationActionHttp(items)
        self.assertTrue(isinstance(action.http_request_action, HTTPRequestAction))

    def test_get_runtime_permissions(self):
        params = {
            "day_time": "morning",
            "deep_link_url": "some_url",
            "icon_url": "some_icon_url"
        }
        settings = {"template_settings": {"project_id": "project_id"}}
        items = {
            "type": "get_runtime_permissions"
        }
        user = PicklableMagicMock()

        expected = {
            "messageName": "GET_RUNTIME_PERMISSIONS",
            "server_action": {
                "parameters": {
                    "need_actions": {
                        "types": ["service_push"]
                    }
                }
            }
        }
        action = GetRuntimePermissionsAction(items)
        user.parametrizer = MockSimpleParametrizer(user, {"data": params})
        user.settings = settings
        text_preprocessing_result = BaseTextPreprocessingResult(items)
        command = action.run(user=user, text_preprocessing_result=text_preprocessing_result)[0]
        self.assertEqual(command.raw, expected)

    def test_push_action_http_with_apprequest_lite_type_request(self):
        items = {
            "type": "push_http",
            "type_request": "apprequest-lite",
            "surface": "COMPANION",
            "access_token": "eyJlbmMiOiJBMjU2Q0JDLUhTNTEyIiwiYWxnIjoiUVAtMjU2In0",
            "callbackUrl": "some_url",
            "templateContent": {
                "id": "49061553-27c7-4471-9145-d8d6137657da",
                "headerValues": {
                    "clientname": "Иван",
                    "bandname": "Ласковый май"
                },
                "bodyValues": {
                    "formatname": "альбома",
                    "bandname": "Ласковый май",
                    "releasename": "Новое"
                }
            }
        }

        templateContent = {
            'id': '49061553-27c7-4471-9145-d8d6137657da',
            'headerValues': {'clientname': 'Иван', 'bandname': 'Ласковый май'},
            'bodyValues': {'formatname': 'альбома', 'bandname': 'Ласковый май', 'releasename': 'Новое'}
        }

        action = PushActionHttp(items)
        self.assertEqual(action.type_request, 'apprequest-lite')
        self.assertEqual(action.templateContent, templateContent)
        self.assertTrue(isinstance(action.http_request_action, HTTPRequestAction))

    def test_push_action_http_with_apprequest_type_request(self):
        payload = {
            'sender':
                {
                    'projectId': '3fa85f64-5717-4562-b3ab-2c963f66baa6',
                    'application':
                        {
                            'appId': None,
                            'versionId': None
                        }
                },
            'recipient':
                {
                    'clientId':
                        {
                            'idType': 'SUB',
                            'id': '6852d76cea737bb751f89e82523a2d97f9765c0d7b8a6eaf821497c1b17df87ba3028e64eea639f7'
                        }
                },
            'deliveryConfig':
                {
                    'deliveryMode': 'broadcast',
                    'destinations':
                        [
                            {
                                'channel': 'COMPANION_B2C',
                                'surface': 'COMPANION',
                                'templateContent':
                                    {
                                        'id': '49061553-27c7-4471-9145-d8d6137657da',
                                        'headerValues':
                                            {
                                                'clientname': 'Иван', 'bandname': 'Ласковый май'
                                            },
                                        'bodyValues':
                                            {
                                                'formatname': 'альбома', 'bandname': 'Ласковый май', 'releasename': 'Новое'
                                            },
                                        'mobileAppParameters':
                                            {
                                                'deeplinkAndroid': 'laskoviyi-mai-listen-android',
                                                'deeplinkIos': 'laskoviyi-mai-listen-ios'
                                            },
                                        'timeFrame':
                                            {
                                                'startTime': '13:30:00',
                                                'finishTime': '15:00:00',
                                                'timeZone': 'GMT+03:00',
                                                'startDate': '2020-06-04',
                                                'endDate': '2020-06-05'
                                            }
                                    }
                            }
                        ]
                }
        }
        items = {
            "type": "push_http",
            "access_token": "eyJlbmMiOiJBMjU2Q0JDLUhTNTEyIiwiYWxnIjoiUVAtMjU2In0",
            "type_request": "apprequest",
            "sender": {
              "projectId": "3fa85f64-5717-4562-b3ab-2c963f66baa6"
            },
            "recipient": {
                "clientId": {
                    "idType": "SUB",
                    "id": "6852d76cea737bb751f89e82523a2d97f9765c0d7b8a6eaf821497c1b17df87ba3028e64eea639f7"
                }
            },
            "deliveryConfig": {
                "deliveryMode": "broadcast",
                "destinations": [
                    {
                        "channel": "COMPANION_B2C",
                        "surface": "COMPANION",
                        "templateContent": {
                            "id": "49061553-27c7-4471-9145-d8d6137657da",
                            "headerValues": {
                                "clientname": "Иван",
                                "bandname": "Ласковый май"
                            },
                            "bodyValues": {
                                "formatname": "альбома",
                                "bandname": "Ласковый май",
                                "releasename": "Новое"
                            },
                            "mobileAppParameters": {
                                "deeplinkAndroid": "laskoviyi-mai-listen-android",
                                "deeplinkIos": "laskoviyi-mai-listen-ios"
                            },
                            "timeFrame": {
                                "startTime": "13:30:00",
                                "finishTime": "15:00:00",
                                "timeZone": "GMT+03:00",
                                "startDate": "2020-06-04",
                                "endDate": "2020-06-05"
                            }
                        }
                    }
                ]
            }
        }

        action = PushActionHttp(items)
        self.assertEqual(action.type_request, 'apprequest')
        self.assertEqual(action.payload, payload)
        self.assertTrue(isinstance(action.http_request_action, HTTPRequestAction))

    @staticmethod
    def set_request_mock_attribute(request_mock, return_value=None):
        return_value = return_value or {}
        request_mock.return_value = Mock(
            __enter__=Mock(return_value=Mock(
                json=Mock(return_value=return_value),
                cookies={},
                headers={},
            ), ),
            __exit__=Mock()
        )

    @patch('requests.request')
    def test_push_authentication_action_http_call(self, request_mock: Mock):
        user = Mock(
            parametrizer=Mock(collect=lambda *args, **kwargs: {}),
            descriptions={
                "behaviors": {
                    "common_behavior": Mock(timeout=Mock(return_value=4))
                }
            }
        )
        self.set_request_mock_attribute(request_mock)
        items = {
            'type': 'push_authentication',
            'client_id': '@!89FB.4D62.3A51.A9EB!0001!96E5.AE89!0008!B1AF.DB7D.1586.84F3',
            'surface': 'COMPANION', 'client_secret': 'secret',
            'nodes': {},
            'command': 'PUSH_NOTIFY',
            'behavior': 'common_behavior',
            'params': {
                'url': 'https://salute.online.sberbank.ru:9443/api/v2/oauth',
                'headers':
                    {
                        'RqUID': '3f68e69e-351b-4e6f-b251-480f0cb08a5d',
                        'Authorization': 'Basic QCE4OUZCLjRENjIuM0E1MS5BOUVCITAwMDEhOTZFNS5BRTg5ITAwMDghQjFBRi5EQjdELjE1ODYuODRGMzpzZWNyZXQ='
                    }
            }
        }

        http_request_action = HTTPRequestAction(items)
        request_body_parameters = {
            "scope": "SMART_PUSH"
        }
        http_request_action.method_params["json"] = request_body_parameters
        http_request_action.run(user, None, None)
        request_mock.assert_called_with(
            url="https://salute.online.sberbank.ru:9443/api/v2/oauth",
            headers={
                'RqUID': '3f68e69e-351b-4e6f-b251-480f0cb08a5d',
                'Authorization': 'Basic QCE4OUZCLjRENjIuM0E1MS5BOUVCITAwMDEhOTZFNS5BRTg5ITAwMDghQjFBRi5EQjdELjE1ODYuODRGMzpzZWNyZXQ='
            },
            method='POST', timeout=4, json=request_body_parameters
        )

    @patch('requests.request')
    def test_push_action_http_call_with_apprequest_lite_type_request(self, request_mock: Mock):
        user = Mock(
            parametrizer=Mock(collect=lambda *args, **kwargs: {}),
            descriptions={
                "behaviors": {
                    "common_behavior": Mock(timeout=Mock(return_value=4))
                }
            }
        )
        self.set_request_mock_attribute(request_mock)
        items = {
            'type': 'push_http',
            'type_request': 'apprequest-lite',
            'surface': 'COMPANION',
            'access_token': 'eyJlbmMiOiJBMjU2Q0JDLUhTNTEyIiwiYWxnIjoiUVAtMjU2In0',
            'callbackUrl': 'some_url',
            'templateContent':
                {
                    'id': '49061553-27c7-4471-9145-d8d6137657da',
                    'headerValues':
                        {
                            'clientname': 'Иван',
                            'bandname': 'Ласковый май'
                        },
                    'bodyValues':
                        {
                            'formatname': 'альбома',
                            'bandname': 'Ласковый май',
                            'releasename': 'Новое'
                        }
                },
            'nodes': {},
            'command': 'PUSH_NOTIFY',
            'params':
                {
                    'url': 'https://salute.online.sberbank.ru:9443/api/v2/smartpush/apprequest-lite',
                    'headers':
                        {
                            'RqUID': '6b27efc2-17f7-4c72-80a3-9a4c349cd07b',
                            'Authorization': 'Bearer eyJlbmMiOiJBMjU2Q0JDLUhTNTEyIiwiYWxnIjoiUVAtMjU2In0',
                            'callbackUrl': 'some_url'
                        },
                    'method': 'POST'
                },
            'behavior': 'common_behavior'
        }
        http_request_action = HTTPRequestAction(items)
        request_body_parameters = {
            'projectId': '83cdd6c6-757a-42ce-b4fe-03912fb7d6e1',
            'clientId': "1596f2a624c003fdb31eb5000e49f1efe8ccf51fd0001f9b499c5881cdca1d95d24e4bf802c48fe0",
            'surface': 'COMPANION',
            'templateContent': {
                'id': '49061553-27c7-4471-9145-d8d6137657da',
                'headerValues':
                    {
                        'clientname': 'Иван',
                        'bandname': 'Ласковый май'
                    },
                'bodyValues':
                    {
                        'formatname': 'альбома',
                        'bandname': 'Ласковый май',
                        'releasename': 'Новое'
                    }
            }
        }
        http_request_action.method_params["json"] = request_body_parameters
        http_request_action.run(user, None, None)
        request_mock.assert_called_with(
            url="https://salute.online.sberbank.ru:9443/api/v2/smartpush/apprequest-lite",
            headers={
                'RqUID': '6b27efc2-17f7-4c72-80a3-9a4c349cd07b',
                'Authorization': 'Bearer eyJlbmMiOiJBMjU2Q0JDLUhTNTEyIiwiYWxnIjoiUVAtMjU2In0',
                'callbackUrl': 'some_url'
            },
            method='POST', timeout=4, json=request_body_parameters
        )

    @patch('requests.request')
    def test_push_action_http_call_with_apprequest_type_request(self, request_mock: Mock):
        user = Mock(
            parametrizer=Mock(collect=lambda *args, **kwargs: {}),
            descriptions={
                "behaviors": {
                    "common_behavior": Mock(timeout=Mock(return_value=4))
                }
            }
        )
        self.set_request_mock_attribute(request_mock)
        items = {
            'type': 'push_http',
            'access_token': 'eyJlbmMiOiJBMjU2Q0JDLUhTNTEyIiwiYWxnIjoiUVAtMjU2In0',
            'type_request': 'apprequest',
            'protocolVersion': 'V1',
            'messageId': '37284759',
            'senderApplication':
                {
                    'appId': '3fa85f64-5717-4562-b3fc-2c963f66afa7',
                    'versionId': 'fcac2f61-57a7-4d6d-b3fc-2c963f66a111'
                },
            'deliveryMode': 'broadcast',
            'destinations':
                [
                    {
                        'channel': 'COMPANION_B2C',
                        'surface': 'COMPANION',
                        'templateContent':
                            {
                                'id': '49061553-27c7-4471-9145-d8d6137657da',
                                'headerValues':
                                    {
                                        'clientname': 'Иван',
                                        'bandname': 'Ласковый май'
                                    },
                                'bodyValues':
                                    {
                                        'formatname': 'альбома',
                                        'bandname': 'Ласковый май',
                                        'releasename': 'Новое'
                                    },
                                'mobileAppParameters':
                                    {
                                        'deeplinkAndroid': 'laskoviyi-mai-listen-android',
                                        'deeplinkIos': 'laskoviyi-mai-listen-ios'
                                    },
                                'timeFrame':
                                    {
                                        'startTime': '13:30:00',
                                        'finishTime': '15:00:00',
                                        'timeZone': 'GMT+03:00',
                                        'startDate': '2020-06-04',
                                        'endDate': '2020-06-05'
                                    }
                            }
                    }
                ],
            'nodes': {},
            'command': 'PUSH_NOTIFY',
            'payload':
                {
                    'sender':
                        {
                            'application':
                                {
                                    'appId': '3fa85f64-5717-4562-b3fc-2c963f66afa7',
                                    'versionId': 'fcac2f61-57a7-4d6d-b3fc-2c963f66a111'
                                }
                        },
                    'recipient':
                        {
                            'clientId':
                                {
                                    'idType': 'SUB'
                                }
                        },
                    'deliveryConfig':
                        {
                            'deliveryMode': 'broadcast',
                            'destinations':
                                [
                                    {
                                        'channel': 'COMPANION_B2C',
                                        'surface': 'COMPANION',
                                        'templateContent':
                                            {
                                                'id': '49061553-27c7-4471-9145-d8d6137657da',
                                                'headerValues':
                                                    {
                                                        'clientname': 'Иван', 'bandname': 'Ласковый май'
                                                    },
                                                'bodyValues':
                                                    {
                                                        'formatname': 'альбома',
                                                        'bandname': 'Ласковый май',
                                                        'releasename': 'Новое'
                                                    },
                                                'mobileAppParameters':
                                                    {
                                                        'deeplinkAndroid': 'laskoviyi-mai-listen-android',
                                                        'deeplinkIos': 'laskoviyi-mai-listen-ios'
                                                    },
                                                'timeFrame':
                                                    {
                                                        'startTime': '13:30:00',
                                                        'finishTime': '15:00:00',
                                                        'timeZone': 'GMT+03:00',
                                                        'startDate': '2020-06-04',
                                                        'endDate': '2020-06-05'
                                                    }
                                            }
                                    }
                                ]
                        }
                },
            'params':
                {
                    'url': 'https://salute.online.sberbank.ru:9443/api/v2/smartpush/apprequest',
                    'headers':
                        {
                            'RqUID': '37f0b5c0-b114-4943-8752-2990f36b3554',
                            'Authorization': 'Bearer eyJlbmMiOiJBMjU2Q0JDLUhTNTEyIiwiYWxnIjoiUVAtMjU2In0',
                            'callbackUrl': None
                        }
                },
            'behavior': 'common_behavior'
        }
        http_request_action = HTTPRequestAction(items)
        request_body_parameters = {
            'protocolVersion': 'V1',
            'messageId': '37284759',
            'messageName': None,
            'payload': {
                'sender':
                    {
                        'application':
                            {
                                'appId': '3fa85f64-5717-4562-b3fc-2c963f66afa7',
                                'versionId': 'fcac2f61-57a7-4d6d-b3fc-2c963f66a111'
                            },
                        'projectId': 'template-app-id'
                    },
                'recipient':
                    {
                        'clientId':
                            {
                                'idType': 'SUB',
                                'id': '6852d76cea737bb751f89e82523a2d97f9765c0d7b8a6eaf821497c1b17df87ba3028e64eea639f7'
                            }
                    },
                'deliveryConfig':
                    {
                        'deliveryMode': 'broadcast',
                        'destinations':
                            [
                                {
                                    'channel': 'COMPANION_B2C',
                                    'surface': 'COMPANION',
                                    'templateContent':
                                        {
                                            'id': '49061553-27c7-4471-9145-d8d6137657da',
                                            'headerValues':
                                                {
                                                    'clientname': 'Иван',
                                                    'bandname': 'Ласковый май'
                                                },
                                            'bodyValues':
                                                {
                                                    'formatname': 'альбома',
                                                    'bandname': 'Ласковый май',
                                                    'releasename': 'Новое'
                                                },
                                            'mobileAppParameters':
                                                {
                                                    'deeplinkAndroid': 'laskoviyi-mai-listen-android',
                                                    'deeplinkIos': 'laskoviyi-mai-listen-ios'
                                                },
                                            'timeFrame':
                                                {
                                                    'startTime': '13:30:00',
                                                    'finishTime': '15:00:00',
                                                    'timeZone': 'GMT+03:00',
                                                    'startDate': '2020-06-04',
                                                    'endDate': '2020-06-05'
                                                }
                                        }
                                }
                            ]
                    }
            }
        }
        http_request_action.method_params["json"] = request_body_parameters
        http_request_action.run(user, None, None)
        request_mock.assert_called_with(
            url="https://salute.online.sberbank.ru:9443/api/v2/smartpush/apprequest",
            headers={
                'RqUID': '37f0b5c0-b114-4943-8752-2990f36b3554',
                'Authorization': 'Bearer eyJlbmMiOiJBMjU2Q0JDLUhTNTEyIiwiYWxnIjoiUVAtMjU2In0'
            },
            method='POST', timeout=4, json=request_body_parameters
        )


class NonRepeatingActionTest(unittest.TestCase):
    def setUp(self):
        self.expected = [PicklableMock()]
        self.expected1 = [PicklableMock()]
        self.action = NonRepeatingAction({"actions": [{"type": "action_mock",
                                                       "result": self.expected},
                                                      {"type": "action_mock",
                                                       "result": self.expected1}
                                                      ],
                                          "last_action_ids_storage": "last_action_ids_storage"})
        self.user = PicklableMagicMock()
        registered_factories[Action] = action_factory
        actions["action_mock"] = MockAction

    def test_run_available_indexes(self):
        self.user.last_action_ids["last_action_ids_storage"].get_list.side_effect = [[0]]
        result = self.action.run(self.user, None)
        self.user.last_action_ids["last_action_ids_storage"].add.assert_called_once()
        self.assertEqual(result, self.expected1)

    def test_run_no_available_indexes(self):
        self.user.last_action_ids["last_action_ids_storage"].get_list.side_effect = [[0, 1]]
        result = self.action.run(self.user, None)
        self.assertEqual(result, self.expected)


class CounterIncrementActionTest(unittest.TestCase):
    def test_run(self):
        user = PicklableMock()
        counter = PicklableMock()
        counter.inc = PicklableMock()
        user.counters = {"test": counter}
        items = {"key": "test"}
        action = CounterIncrementAction(items)
        action.run(user, None)
        user.counters["test"].inc.assert_called_once()


class CounterDecrementActionTest(unittest.TestCase):
    def test_run(self):
        user = PicklableMock()
        counter = PicklableMock()
        counter.dec = PicklableMock()
        user.counters = {"test": counter}
        items = {"key": "test"}
        action = CounterDecrementAction(items)
        action.run(user, None)
        user.counters["test"].dec.assert_called_once()


class CounterClearActionTest(unittest.TestCase):
    def test_run(self):
        user = PicklableMock()
        user.counters = PicklableMock()
        user.counters.inc = PicklableMock()
        items = {"key": "test"}
        action = CounterClearAction(items)
        action.run(user, None)
        user.counters.clear.assert_called_once()


class CounterSetActionTest(unittest.TestCase):
    def test_run(self):
        user = PicklableMock()
        counter = PicklableMock()
        counter.inc = PicklableMock()
        counters = {"test": counter}
        user.counters = counters
        items = {"key": "test"}
        action = CounterSetAction(items)
        action.run(user, None)
        user.counters["test"].set.assert_called_once()


class CounterCopyActionTest(unittest.TestCase):
    def test_run(self):
        user = PicklableMock()
        counter_src = PicklableMock()
        counter_src.value = 10
        counter_dst = PicklableMock()
        user.counters = {"src": counter_src, "dst": counter_dst}
        items = {"source": "src", "destination": "dst"}
        action = CounterCopyAction(items)
        action.run(user, None)
        user.counters["dst"].set.assert_called_once_with(user.counters["src"].value,
                                                         action.reset_time, action.time_shift)


class AfinaAnswerActionTest(unittest.TestCase):
    def test_typical_answer(self):
        user = PicklableMock()
        user.parametrizer = MockParametrizer(user, {})
        expected = [MagicMock(_name="ANSWER_TO_USER", raw={'messageName': 'ANSWER_TO_USER',
                                                           'payload': {'answer': 'a1'}})]
        items = {
            "nodes": {
                "answer": ["a1", "a1", "a1"],
            }
        }
        action = AfinaAnswerAction(items)

        result = action.run(user, None)
        self.assertEqual(expected[0]._name, result[0].name)
        self.assertEqual(expected[0].raw, result[0].raw)

    def test_typical_answer_with_other(self):
        user = PicklableMock()
        user.parametrizer = MockParametrizer(user, {})
        expected = [MagicMock(_name="ANSWER_TO_USER", raw={'messageName': 'ANSWER_TO_USER',
                                                           'payload': {'answer': 'a1',
                                                                       "pronounce_text": 'pt2',
                                                                       "picture": "1.jpg"}})]
        items = {
            "nodes": {
                "answer": ["a1", "a1", "a1"],
                "pronounce_text": ["pt2"],
                "picture": ["1.jpg", "1.jpg", "1.jpg"]
            }
        }
        action = AfinaAnswerAction(items)

        result = action.run(user, None)
        self.assertEqual(expected[0]._name, result[0].name)
        self.assertEqual(expected[0].raw, result[0].raw)

    def test_typical_answer_with_pers_info(self):
        expected = [MagicMock(_name="ANSWER_TO_USER", raw={'messageName': 'ANSWER_TO_USER',
                                                           'payload': {'answer': 'Ivan Ivanov'}})]
        user = PicklableMock()
        user.parametrizer = MockParametrizer(user, {})
        user.message = PicklableMock()
        user.message.payload = {"personInfo": {"name": "Ivan Ivanov"}}
        items = {"nodes": {"answer": ["{{payload.personInfo.name}}"]}}
        action = AfinaAnswerAction(items)
        result = action.run(user, None)
        self.assertEqual(expected[0]._name, result[0].name)
        self.assertEqual(expected[0].raw, result[0].raw)

    def test_items_empty(self):
        user = PicklableMock()
        user.parametrizer = MockParametrizer(user, {})
        template = PicklableMock()
        template.get_template = Mock(return_value=[])
        user.descriptions = {"render_templates": template}
        items = None
        action = AfinaAnswerAction(items)
        result = action.run(user, None)
        self.assertEqual(result, [])

    def test__items_empty_dict(self):
        user = PicklableMock()
        user.parametrizer = MockParametrizer(user, {})
        template = PicklableMock()
        template.get_template = Mock(return_value=[])
        user.descriptions = {"render_templates": template}
        items = {}
        action = AfinaAnswerAction(items)
        result = action.run(user, None)
        self.assertEqual(result, [])


class CardAnswerActionTest(unittest.TestCase):
    def test_typical_answer(self):
        user = PicklableMock()
        user.parametrizer = MockParametrizer(user, {})
        user.message = PicklableMock()
        user.message.payload = {"personInfo": {"name": "Ivan Ivanov"}}
        items = {
            "type": "sdk_answer",
            "nodes": {
                "pronounceText": ["pronounceText1", "{{payload.personInfo.name}}"],
                "items": [
                  {
                    "bubble": {
                      "text": ["Text1", "Text2"]
                    }
                  },
                  {
                    "card": {
                      "type": "simple_list",
                      "header": "1 доллар США ",
                      "items": [
                        {
                          "title": "Купить",
                          "body": "67.73 RUR"
                        },
                        {
                          "title": "Продать",
                          "body": "64.56 RUR"
                        }
                      ],
                      "footer": "{{payload.personInfo.name}} Сбербанк Онлайн на сегодня 17:53 при обмене до 1000 USD"
                    }
                  }
                ],
                "suggestions": {
                     "buttons": [{
                        "title": ["Отделения"],
                        "action": {
                          "text": "Где ближайщие отделения сбера?",
                          "type": "text"
                        }
                     }]
                }
            }
        }
        exp1 = json.dumps({'messageName': 'ANSWER_TO_USER', 'payload': {'pronounceText': 'Ivan Ivanov', 'items': [{'bubble': {'text': 'Text2'}}, {'card': {'type': 'simple_list', 'header': '1 доллар США ', 'items': [{'title': 'Купить', 'body': '67.73 RUR'}, {'title': 'Продать', 'body': '64.56 RUR'}], 'footer': 'Ivan Ivanov Сбербанк Онлайн на сегодня 17:53 при обмене до 1000 USD'}}], 'suggestions': {'buttons': [{'title': 'Отделения', 'action': {'text': 'Где ближайщие отделения сбера?', 'type': 'text'}}]}}}, sort_keys=True)
        exp2 = json.dumps({'messageName': 'ANSWER_TO_USER', 'payload': {'pronounceText': 'pronounceText1', 'items': [{'bubble': {'text': 'Text1'}}, {'card': {'type': 'simple_list', 'header': '1 доллар США ', 'items': [{'title': 'Купить', 'body': '67.73 RUR'}, {'title': 'Продать', 'body': '64.56 RUR'}], 'footer': 'Ivan Ivanov Сбербанк Онлайн на сегодня 17:53 при обмене до 1000 USD'}}], 'suggestions': {'buttons': [{'title': 'Отделения', 'action': {'text': 'Где ближайщие отделения сбера?', 'type': 'text'}}]}}}, sort_keys=True)
        expect_arr = [exp1, exp2]

        nexp1 = json.dumps({'messageName': 'ANSWER_TO_USER', 'payload': {'pronounceText': 'Ivan Ivanov', 'items': [{'bubble': {'text': 'Text1'}}, {'card': {'type': 'simple_list', 'header': '1 доллар США ', 'items': [{'title': 'Купить', 'body': '67.73 RUR'}, {'title': 'Продать', 'body': '64.56 RUR'}], 'footer': 'Ivan Ivanov Сбербанк Онлайн на сегодня 17:53 при обмене до 1000 USD'}}], 'suggestions': {'buttons': [{'title': 'Отделения', 'action': {'text': 'Где ближайщие отделения сбера?', 'type': 'text'}}]}}}, sort_keys=True)
        nexp2 = json.dumps({'messageName': 'ANSWER_TO_USER', 'payload': {'pronounceText': 'pronounceText1', 'items': [{'bubble': {'text': 'Text2'}}, {'card': {'type': 'simple_list', 'header': '1 доллар США ', 'items': [{'title': 'Купить', 'body': '67.73 RUR'}, {'title': 'Продать', 'body': '64.56 RUR'}], 'footer': 'Ivan Ivanov Сбербанк Онлайн на сегодня 17:53 при обмене до 1000 USD'}}], 'suggestions': {'buttons': [{'title': 'Отделения', 'action': {'text': 'Где ближайщие отделения сбера?', 'type': 'text'}}]}}}, sort_keys=True)
        not_expect_arr = [nexp1, nexp2]

        for i in range(10):
            action = SDKAnswer(items)
            result = action.run(user, None)
            self.assertEqual("ANSWER_TO_USER", result[0].name)
            self.assertTrue(json.dumps(result[0].raw, sort_keys=True) in expect_arr)
            self.assertFalse(json.dumps(result[0].raw, sort_keys=True) in not_expect_arr)


    def test_typical_answer_without_items(self):
        user = PicklableMock()
        user.parametrizer = MockParametrizer(user, {})
        user.message = PicklableMock()
        user.message.payload = {"personInfo": {"name": "Ivan Ivanov"}}
        items = {
            "type": "sdk_answer",
            "nodes": {
                "pronounceText": ["pronounceText1", "pronounceText2"],
            }
        }
        exp1 = json.dumps({'messageName': 'ANSWER_TO_USER', 'payload': {'pronounceText': 'pronounceText1'}}, sort_keys=True)
        exp2 = json.dumps({'messageName': 'ANSWER_TO_USER', 'payload': {'pronounceText': 'pronounceText2'}}, sort_keys=True)
        exp_list = [exp1, exp2]
        for i in range(10):
            action = SDKAnswer(items)
            result = action.run(user, None)
            self.assertEqual("ANSWER_TO_USER", result[0].name)
            self.assertTrue(json.dumps((result[0].raw), sort_keys=True) in exp_list)

    def test_typical_answer_without_nodes(self):
        user = PicklableMock()
        user.parametrizer = MockParametrizer(user, {})
        user.message = PicklableMock()
        user.message.payload = {"personInfo": {"name": "Ivan Ivanov"}}
        items = {
                "type": "sdk_answer",
                "pronounceText": ["pronounceText1"],
                "suggestions": {
                    "buttons": [
                        {
                            "title": ["{{payload.personInfo.name}}", "отделения2"],
                            "action": {
                                "text": "отделения",
                                "type": "text"
                            }
                        },
                        {
                            "title": ["кредит1", "кредит2"],
                            "action": {
                                "text": "кредит",
                                "type": "text"
                            }
                        }
                    ]
                }
        }
        exp1 = json.dumps({'messageName': 'ANSWER_TO_USER', 'payload': {'pronounceText': 'pronounceText1', 'suggestions': {'buttons': [{'title': 'Ivan Ivanov', 'action': {'text': 'отделения', 'type': 'text'}}, {'title': 'кредит1', 'action': {'text': 'кредит', 'type': 'text'}}]}}}, sort_keys=True)
        exp2 = json.dumps({'messageName': 'ANSWER_TO_USER', 'payload': {'pronounceText': 'pronounceText1', 'suggestions': {'buttons': [{'title': 'отделения2', 'action': {'text': 'отделения', 'type': 'text'}}, {'title': 'кредит2', 'action': {'text': 'кредит', 'type': 'text'}}]}}}, sort_keys=True)
        expect_arr = [exp1, exp2]

        nexp1 = json.dumps({'messageName': 'ANSWER_TO_USER', 'payload': {'pronounceText': 'pronounceText1', 'suggestions': {'buttons': [{'title': 'Ivan Ivanov', 'action': {'text': 'отделения', 'type': 'text'}}, {'title': 'кредит2', 'action': {'text': 'кредит', 'type': 'text'}}]}}}, sort_keys=True)
        nexp2 = json.dumps({'messageName': 'ANSWER_TO_USER', 'payload': {'pronounceText': 'pronounceText1', 'suggestions': {'buttons': [{'title': 'отделения2', 'action': {'text': 'отделения', 'type': 'text'}}, {'title': 'кредит1', 'action': {'text': 'кредит', 'type': 'text'}}]}}}, sort_keys=True)
        not_expect_arr = [nexp1, nexp2]
        for i in range(10):
            action = SDKAnswer(items)
            result = action.run(user, None)
            self.assertEqual("ANSWER_TO_USER", result[0].name)
            self.assertTrue(json.dumps((result[0].raw), sort_keys=True) in expect_arr)
            self.assertFalse(json.dumps((result[0].raw), sort_keys=True) in not_expect_arr)


class SDKRandomAnswer(unittest.TestCase):
    def test_SDKItemAnswer_full(self):

        registered_factories[SdkAnswerItem] = items_factory
        answer_items["bubble_text"] = BubbleText
        answer_items["item_card"] = ItemCard
        answer_items["pronounce_text"] = PronounceText
        answer_items["suggest_text"] = SuggestText
        answer_items["suggest_deeplink"] = SuggestDeepLink

        registered_factories[Requirement] = requirement_factory
        requirements["test"] = MockRequirement
        requirements[None] = Requirement

        user = PicklableMock()
        user.parametrizer = MockParametrizer(user, {})
        user.message = PicklableMock()
        user.message.payload = {"personInfo": {"name": "Ivan Ivanov"}}
        items = {
            "type": "sdk_answer_to_user",
            "static":
                {
                    "static_text": "st1",
                    "card1": {"cards_params": "a lot of params"},
                    "dl": "www.ww.w"
                },
            "random_choice": [
                {
                    "pron": "p1",
                    "txt": "{{payload.personInfo.name}}",
                    "title": "title1"
                },
                {
                    "pron": "p2",
                    "txt": "t2",
                    "title": "title2"
                }],
            "items":
                [
                    {
                        'type': "item_card",
                        "text": "txt",
                        "requirement": {"type": "test", "result": False}
                    },
                    {
                        'type': "bubble_text",
                        "text": "txt",
                        "markdown": False
                    },
                    {
                        'type': "item_card",
                        "text": "card1",
                        "requirement": {"type": "test", "result": True}
                    }
                ],
            "root":
                [
                    {
                        'type': "pronounce_text",
                        "text": "pron",
                    }
                ],
            "suggestions":
                [
                    {
                        "type": "suggest_text",
                        "title": "pron",
                        "text": "txt",
                    },
                    {
                        "type": "suggest_text",
                        "title": "pron",
                        "text": "txt",
                        "requirement": {"type": "test", "result": True}
                    },
                    {
                        "type": "suggest_deeplink",
                        "title": "pron",
                        "deep_link": "dl"
                    }
                ]
        }
        exp1 = json.dumps({'messageName': 'ANSWER_TO_USER', 'payload': {'items': [{'bubble': {'text': 't2', 'markdown': False}}, {'card': {'cards_params': 'a lot of params'}}], 'suggestions': {'buttons': [{'title': 'p2', 'action': {'text': 't2', 'type': 'text'}}, {'title': 'p2', 'action': {'text': 't2', 'type': 'text'}}, {'title': 'p2', 'action': {'deep_link': 'www.ww.w', 'type': 'deep_link'}}]}, 'pronounceText': 'p2'}}, sort_keys=True)
        exp2 = json.dumps({'messageName': 'ANSWER_TO_USER', 'payload': {'items': [{'bubble': {'text': 'Ivan Ivanov', 'markdown': False}}, {'card': {'cards_params': 'a lot of params'}}], 'suggestions': {'buttons': [{'title': 'p1', 'action': {'text': 'Ivan Ivanov', 'type': 'text'}}, {'title': 'p1', 'action': {'text': 'Ivan Ivanov', 'type': 'text'}}, {'title': 'p1', 'action': {'deep_link': 'www.ww.w', 'type': 'deep_link'}}]}, 'pronounceText': 'p1'}}, sort_keys=True)

        action = SDKAnswerToUser(items)
        for i in range(3):
            result = action.run(user, None)
            self.assertTrue(json.dumps(result[0].raw, sort_keys=True) in [exp1, exp2])

    def test_SDKItemAnswer_root(self):

        registered_factories[SdkAnswerItem] = items_factory
        answer_items["bubble_text"] = BubbleText
        answer_items["item_card"] = ItemCard
        answer_items["pronounce_text"] = PronounceText
        answer_items["suggest_text"] = SuggestText
        answer_items["suggest_deeplink"] = SuggestDeepLink


        user = PicklableMock()
        user.parametrizer = MockParametrizer(user, {})
        user.message = PicklableMock()
        user.message.payload = {"personInfo": {"name": "Ivan Ivanov"}}
        items = {
            "type": "sdk_answer_to_user",
            "static":
                {
                    "static_text": "st1",
                    "card1": {"cards_params": "a lot of params"},
                    "dl": "www.ww.w"
                },
            "random_choice": [
                {
                    "pron": "p1",
                    "txt": "{{payload.personInfo.name}}",
                    "title": "title1"
                },
                {
                    "pron": "p2",
                    "txt": "t2",
                    "title": "title2"
                }],
            "root":
                [
                    {
                        'type': "pronounce_text",
                        "text": "pron",
                    },
                ]
        }
        exp1 = json.dumps({'messageName': 'ANSWER_TO_USER', 'payload': {'pronounceText': 'p1'}}, sort_keys=True)
        exp2 = json.dumps({'messageName': 'ANSWER_TO_USER', 'payload': {'pronounceText': 'p2'}}, sort_keys=True)

        action = SDKAnswerToUser(items)
        for i in range(3):
            result = action.run(user, None)
            self.assertTrue(json.dumps(result[0].raw, sort_keys=True) in [exp1, exp2])

    def test_SDKItemAnswer_simple(self):

        registered_factories[SdkAnswerItem] = items_factory
        answer_items["bubble_text"] = BubbleText

        user = PicklableMock()
        user.parametrizer = MockParametrizer(user, {})
        items = {
            "type": "sdk_answer_to_user",
            "items":
                [
                    {
                        'type': "bubble_text",
                        "text": "42"
                    }
                ]
        }
        action = SDKAnswerToUser(items)
        result = action.run(user, None)
        self.assertDictEqual(result[0].raw, {'messageName': 'ANSWER_TO_USER', 'payload': {'items': [{'bubble': {'text': '42', 'markdown': True}}]}})

    def test_SDKItemAnswer_suggestions_template(self):

        registered_factories[SdkAnswerItem] = items_factory
        answer_items["bubble_text"] = BubbleText

        user = PicklableMock()
        user.parametrizer = MockParametrizer(user, {})
        items = {
            "type": "sdk_answer_to_user",
            "support_templates": {
                "suggestions_from_template": '{ "buttons": [ { "title": "some title", "action": { "type": "text", "text": "some text" } } ]}'
            },
            "suggestions_template": {
                "type": "unified_template",
                "template": "{{ suggestions_from_template }}",
                "loader": "json"
            }
        }
        action = SDKAnswerToUser(items)
        result = action.run(user, None)
        self.assertDictEqual(
            result[0].raw,
            {
                'messageName': 'ANSWER_TO_USER',
                'payload': {
                    'suggestions': {
                        'buttons': [
                            {'title': 'some title', 'action': {'type': 'text', 'text': 'some text'}}
                        ]
                    }
                }
            })


class GiveMeMemoryActionTest(unittest.TestCase):
    @patch("smart_kit.configs.settings.Settings")
    def test_run(self, settings_mock: MagicMock):
        expected = [
            Command("GIVE_ME_MEMORY",
                    {
                        'root_nodes': {
                            'protocolVersion': 1
                        },
                        'consumer': {
                            'projectId': '0'
                        },
                        "tokenType": 0,
                        'profileEmployee': 0,
                        'memory': [
                            {
                                'memoryPartition': 'confidentialMemo',
                                'tags': [
                                    'userAgreement',
                                    'userAgreementProject'
                                ]
                            },
                            {
                                'memoryPartition': 'projectPrivateMemo',
                                'tags': [
                                    'test'
                                ]
                            }
                        ]
                    },
                    None, "kafka", {"topic_key": "client_info", "kafka_key": "main", "kafka_replyTopic": "app"})
        ]
        user = PicklableMagicMock()
        params = {"params": "params"}
        user.parametrizer = MockSimpleParametrizer(user, {"data": params})
        settings = {
            "template_settings": {
                "project_id": "0",
                "consumer_topic": "app"
            }
        }
        settings_mock.return_value = settings
        items = {
            "behavior": "my_behavior",
            "nodes": {
                "memory": {
                    "confidentialMemo": [
                        "userAgreement",
                        "userAgreementProject"
                    ],
                    "projectPrivateMemo": [
                        "{{ 'test' }}"
                    ]
                },
                "profileEmployee": {
                    "type": "unified_template",
                    "template": "{{ 0 }}",
                    "loader": "json"
                },
                "tokenType": {
                    "type": "unified_template",
                    "template": "{{ 0 }}",
                    "loader": "json"
                }
            }
        }
        text_preprocessing_result = PicklableMock()
        action = GiveMeMemoryAction(items)
        result = action.run(user, text_preprocessing_result)
        self.assertEqual(expected[0].name, result[0].name)
        self.assertEqual(expected[0].payload, result[0].payload)


class RememberThisActionTest(unittest.TestCase):
    def test_run(self):
        expected = [
            Command("REMEMBER_THIS",
                    {
                        'root_nodes': {
                            'protocolVersion': 3
                        },
                        'consumer': {
                            'projectId': '0'
                        },
                        'clientIds': 0,
                        'memory': [
                            {
                                'memoryPartition': 'publicMemo',
                                'partitionData': [
                                    {
                                        'tag': 'historyInfo',
                                        'action': {
                                            'type': 'upsert',
                                            'params': {
                                                'operation': [
                                                    {
                                                        'selector': {
                                                            'intent': {
                                                                '$eq': 'run_app'
                                                            },
                                                            'surface': {
                                                                '$eq': '0'
                                                            },
                                                            'channel': {
                                                                '$eq': '0'
                                                            },
                                                            'projectId': {
                                                                '$eq': '0'
                                                            }
                                                        },
                                                        'updater': [
                                                            {
                                                                '$set': {
                                                                    '$.lastExecuteDateTime': '0'
                                                                }
                                                            },
                                                            {
                                                                '$inc': {
                                                                    '$.executeCounter': 1
                                                                }
                                                            }
                                                        ]
                                                    }
                                                ]
                                            }
                                        }
                                    }
                                ]
                            }
                        ]
                    },
                    None, "kafka", {
                        "topic_key": 'client_info_remember',
                        "kafka_key": "main",
                        "kafka_replyTopic": "app"
                    })
        ]
        user = PicklableMagicMock()
        user.settings = {
            "template_settings": {
                "project_id": "0",
                "consumer_topic": "app"
            }
        }
        params = {"params": "params"}
        user.parametrizer = MockSimpleParametrizer(user, {"data": params})
        items = {
            "nodes": {
              "clientIds": {
                "type": "unified_template",
                "template": "{{ 0 }}",
                "loader": "json"
              },
              "memory": [
                {
                  "memoryPartition": "publicMemo",
                  "partitionData": [
                    {
                      "tag": "historyInfo",
                      "action": {
                        "type": "upsert",
                        "params": {
                          "operation": [
                            {
                              "selector": {
                                "intent": {
                                  "$eq": "run_app"
                                },
                                "surface": {
                                  "$eq": "{{ 0 }}"
                                },
                                "channel": {
                                  "$eq": "{{ 0 }}"
                                },
                                "projectId": {
                                  "$eq": "{{ 0 }}"
                                }
                              },
                              "updater": [
                                {
                                  "$set": {
                                    "$.lastExecuteDateTime": "{{ 0 }}"
                                  }
                                },
                                {
                                  "$inc": {
                                    "$.executeCounter": 1
                                  }
                                }
                              ]
                            }
                          ]
                        }
                      }
                    }
                  ]
                }
              ]
            }
        }
        action = RememberThisAction(items)
        result = action.run(user, None)
        self.assertEqual(expected[0].name, result[0].name)
        self.assertEqual(expected[0].payload, result[0].payload)

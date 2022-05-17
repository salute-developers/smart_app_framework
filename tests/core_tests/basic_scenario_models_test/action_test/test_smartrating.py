import unittest
from unittest.mock import patch, MagicMock

import smart_kit
from core.basic_models.actions.command import Command
from core.basic_models.actions.smartrating import CallRatingAction, AskRatingAction
from smart_kit.utils.picklable_mock import PicklableMagicMock
from tests.core_tests.basic_scenario_models_test.action_test.test_action import MockSimpleParametrizer


class CallRatingActionTest(unittest.TestCase):
    @patch("smart_kit.configs.settings.Settings")
    def test_run(self, settings_mock: MagicMock):
        expected = [Command("CALL_RATING", {}, None, "kafka",
                            {"topic_key": "toDP", "kafka_key": "main", "kafka_replyTopic": "app"})]
        user = PicklableMagicMock()
        params = {"params": "params"}
        user.parametrizer = MockSimpleParametrizer(user, {"data": params})
        settings_mock.return_value = {
            "template_settings": {
                "project_id": "0"
            },
            "kafka": {
                "template-engine": {
                    "main": {
                        "consumer": {
                            "topics": {
                                "smartrating": "app"
                            }
                        }
                    }
                }
            }
        }
        items = {}
        action = CallRatingAction(items)
        result = action.run(user, None)
        self.assertEqual(expected[0].name, result[0].name)
        self.assertEqual(expected[0].payload, result[0].payload)
        self.assertEqual(expected[0].request_data, result[0].request_data)


class AskRatingActionTest(unittest.TestCase):
    @patch("smart_kit.configs.settings.Settings")
    def test_run(self, settings_mock: MagicMock):
        expected = [Command("ASK_RATING", {}, None, "kafka",
                            {"topic_key": "toDP", "kafka_key": "main", "kafka_replyTopic": "app"})]
        user = PicklableMagicMock()
        params = {"params": "params"}
        user.parametrizer = MockSimpleParametrizer(user, {"data": params})
        settings_mock.return_value = {
            "template_settings": {
                "project_id": "0"
            },
            "kafka": {
                "template-engine": {
                    "main": {
                        "consumer": {
                            "topics": {
                                "smartrating": "app"
                            }
                        }
                    }
                }
            }
        }
        items = {}
        action = AskRatingAction(items)
        result = action.run(user, None)
        self.assertEqual(expected[0].name, result[0].name)
        self.assertEqual(expected[0].payload, result[0].payload)
        self.assertEqual(expected[0].request_data, result[0].request_data)

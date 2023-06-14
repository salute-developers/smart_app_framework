import json
import unittest
from logging import LogRecord
from typing import Dict, Any
from unittest.mock import Mock

from smart_kit.utils.logger_writer.logger_formatter import SmartKitJsonFormatter


class SmartKitJsonFormatterTest(unittest.TestCase):
    def setUp(self):
        self.items = {
            "json_ensure_ascii": False,
            "fields_type": {
                "request_app_type_ok": {
                    "type": "bool"
                },
                "request_data": {
                    "fields": {
                        "kafka_key": {
                            "type": "str"
                        },
                        "topic": {
                            "type": "str"
                        },
                        "topic_key": {
                            "type": "str"
                        },
                        "icon": {
                            "fields": {
                                "hash": {
                                    "type": "int"
                                },
                                "type": {
                                    "type": "str"
                                },
                                "url": {
                                    "type": "str"
                                }
                            },
                            "type": "dict"
                        },
                    },
                    "type": "dict"
                },
                "when": {
                    "type": "int"
                },
                "worker_id": {
                    "type": "str"
                }
            }
        }
        self.formatter = SmartKitJsonFormatter(**self.items)

    @staticmethod
    def mock_log_record(args: Dict[str, Any]):
        return LogRecord("name", 40, 'pathname', 145, 'msg', [args], None)

    def format_and_loads(self, args: Dict[str, Any]):
        record = self.mock_log_record(args)
        return json.loads(self.formatter.format(record))

    def test_int_no_changes(self):
        self.assertEqual(self.format_and_loads(args={"when": 0})["args"]["when"], 0)

    def test_cast_str_int(self):
        self.assertEqual(self.format_and_loads(args={"when": "0"})["args"]["when"], 0)

    def test_cast_str_int_no_cast(self):
        args = self.format_and_loads(args={"when": "test"})["args"]
        self.assertNotIn("when", args)
        self.assertEqual(args["when__str"], "test")

    def test_cast_str_float(self):
        self.assertEqual(self.format_and_loads(args={"when": "0.7"})["args"]["when"], 0.7)

    def test_str_no_changes(self):
        self.assertEqual(self.format_and_loads(args={"worker_id": "0"})["args"]["worker_id"], "0")

    def test_cast_int_to_str(self):
        self.assertEqual(self.format_and_loads(args={"worker_id": 0})["args"]["worker_id"], "0")

    def test_cast_dict_to_str(self):
        self.assertEqual(self.format_and_loads(args={"worker_id": {"a": 0}})["args"]["worker_id"], "{'a': 0}")

    def test_cast_empty_dict(self):
        self.assertEqual(self.format_and_loads(args={"request_data": {}})["args"]["request_data"], {})

    def test_dict_no_cast(self):
        self.assertEqual(self.format_and_loads(args={"request_data": {
            "kafka_key": 'a',
            "topic": 'b',
            "topic_key": 'c',
        }})["args"]["request_data"], {'topic': 'b', 'kafka_key': 'a', 'topic_key': 'c'})

    def test_dict_cast_int_str(self):
        self.assertEqual(self.format_and_loads(args={"request_data": {
            "kafka_key": 0,
            "topic": 1,
            "topic_key": 'c',
        }})["args"]["request_data"], {'kafka_key': '0', 'topic': '1', 'topic_key': 'c'})

    def test_nested_dict_no_cast(self):
        self.assertEqual(self.format_and_loads(args={"request_data": {
            "kafka_key": 0,
            "topic": 1,
            "topic_key": 'c',
            "icon": {"hash": 123, "type": "jpg"}
        }})["args"]["request_data"], {
            "kafka_key": '0',
            "topic": '1',
            "topic_key": 'c',
            "icon": {"hash": 123, "type": "jpg"}
        })

    def test_nested_dict_cast_str_int(self):
        self.assertEqual(self.format_and_loads(args={"request_data": {
            "kafka_key": 0,
            "topic": 1,
            "topic_key": 'c',
            "icon": {"hash": "123", "type": "jpg"}
        }})["args"]["request_data"], {
            "kafka_key": '0',
            "topic": '1',
            "topic_key": 'c',
            "icon": {"hash": 123, "type": "jpg"}
        })

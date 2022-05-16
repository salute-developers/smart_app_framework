# coding: utf-8
import json
import unittest
from unittest.mock import Mock

from smart_kit.message.as_is_to_message import AsIsToMessage


class TestAsIsTooMessage(unittest.TestCase):
    def setUp(self):
        self.command_ = Mock()
        self.request_ = Mock()
        self.message_ = Mock()
        self.command_.loader = "json.dumps"
        self.request_.header = "json"
        self.command_.payload = {}
        self.command_.root_nodes = {}
        self.command_.raw = {
            "content": {"test_param": ""},
            "surface": "some_surface",
            "project_id": "project_id",
        }
        self.message_.sub = 'sub'

    def test_as_is_to_message_as_dict(self):
        obj = AsIsToMessage(self.command_, self.message_, self.request_)
        self.assertEqual(obj.as_dict, {
            "content": {"test_param": ""},
            "surface": "some_surface",
            "project_id": "project_id"})

# coding: utf-8
import unittest
from unittest.mock import Mock, MagicMock

from smart_kit.handlers.handler_take_profile_data import HandlerTakeProfileData, GEO


async def success(x):
    yield "success"


async def fail(x):
    yield "fail"


async def timeout(x):
    yield "timeout"


class MockVariables(Mock):
    _storage = {}

    def set(self, x, y):
        self._storage[x] = y

    def __getitem__(self, item):
        return self._storage[item]

    def get(self, item, default=None):
        if item in self._storage:
            return self._storage[item]
        return default


class HandleTakeProfileDataTest(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.app_name = "TestAppName"
        self.test_payload_1 = {"server_action": {}}
        self.test_payload_2 = {"server_action": {"action_id": 1, "parameters": 1}}

        def behavior_outcome(result):
            async def outcome(x):
                for command in result:
                    yield command
            return outcome

        self.test_user = MagicMock('user', message=MagicMock(message_name="some_name"), variables=MockVariables(),
                                   behaviors=MagicMock(success=behavior_outcome(["success"]),
                                                       fail=behavior_outcome(["fail"]),
                                                       timeout=behavior_outcome(["timeout"])))

    async def test_handle_take_profile_data_init(self):
        obj = HandlerTakeProfileData(self.app_name)
        self.assertIsNotNone(obj.SUCCESS_CODE)
        self.assertIsNotNone(GEO)

    async def test_handle_take_profile_data_run_fail(self):
        obj = HandlerTakeProfileData(self.app_name)
        payload = {"status_code": {"code": 102}}
        result = []
        async for command in obj.run(payload, self.test_user):
            result.append(command)
        self.assertEqual(result, ["fail"])

    async def test_handle_take_profile_data_run_success(self):
        obj = HandlerTakeProfileData(self.app_name)
        payload = {"profile_data": {"geo": {"reverseGeocoding": {"country": "Российская Федерация"},
                                            "location": {"lat": 10.125, "lon": 10.0124}}},
                   "status_code": {"code": 1}}
        result = []
        async for command in obj.run(payload, self.test_user):
            result.append(command)
        self.assertEqual(result, ["success"])
        self.assertEqual(self.test_user.variables.get("smart_geo"), payload["profile_data"]["geo"])

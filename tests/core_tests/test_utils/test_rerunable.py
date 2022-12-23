from unittest import TestCase
from unittest.mock import Mock

from core.utils.rerunable import Rerunable
from smart_kit.utils.picklable_mock import PicklableMock


class HandledException(Exception):
    pass


class AllFailedException(Exception):
    pass


class CustomException(Exception):
    pass


class RerunableOne(Rerunable):
    def __init__(self, try_count):
        super(RerunableOne, self).__init__({"try_count": try_count})
        self._on_prepare_mock = PicklableMock()

    @property
    def _handled_exception(self):
        return HandledException

    def _on_prepare(self):
        self._on_prepare_mock()

    def _on_all_tries_fail(self):
        raise AllFailedException

    def run(self, *args, **kwargs):
        return self._run(*args, **kwargs)


class TestRerunable(TestCase):
    def setUp(self):
        self.try_count = 2
        self.rerunable = RerunableOne(self.try_count)
        self.expected_value = PicklableMock()
        self.param = PicklableMock()
        self.param1 = {"param1_name": PicklableMock()}

    def test_pass(self):
        self.action = PicklableMock()
        self.rerunable.run(self.action, self.param, **self.param1)
        self.action.assert_called_once_with(self.param, **self.param1)

    def test_wrong_exception(self):
        self.action = Mock(side_effect=CustomException())
        with self.assertRaises(CustomException):
            self.rerunable.run(self.action, self.param, **self.param1)
        self.action.assert_called_once_with(self.param, **self.param1)

    def test_all_retry_failed(self):
        self.action = Mock(side_effect=HandledException())
        with self.assertRaises(AllFailedException):
            self.rerunable.run(self.action, self.param, **self.param1)
        self.action.assert_called_with(self.param, **self.param1)
        self.assertEqual(self.action.call_count, self.try_count)

    def test_first_try_failed(self):
        self.param = PicklableMock()
        self.param1 = {"param1_name": PicklableMock()}
        self.action = Mock(side_effect=[HandledException(), self.expected_value])
        result = self.rerunable.run(self.action, self.param, **self.param1)
        self.action.assert_called_with(self.param, **self.param1)
        self.assertEqual(self.action.call_count, self.try_count)
        self.assertEqual(result, self.expected_value)

    def test_first_try_ok(self):
        self.action = Mock(return_value=self.expected_value)
        result = self.rerunable.run(self.action, self.param, **self.param1)
        self.action.assert_called_once_with(self.param, **self.param1)
        self.assertEqual(result, self.expected_value)

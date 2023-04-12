# coding: utf-8
import unittest
from unittest.mock import Mock, patch

from smart_kit.management.tests import TestsCommand


class SystemAnswersTest1(unittest.IsolatedAsyncioTestCase):  # TODO тесты на manage.py tests
    def setUp(self):
        pass

    async def test_run(self):
        app_config = Mock(SSML_TEST_ADDRESS="")
        tests_command = TestsCommand(app_config)
        self.assertRaises(SystemExit, tests_command.execute, "--run")

    async def test_run_path(self):
        app_config = Mock(SSML_TEST_ADDRESS="")
        tests_command = TestsCommand(app_config)
        tests_command.run_scenario_tests = Mock(return_value=True)
        tests_command.run_ssml_tests = Mock(return_value=True)
        tests_command.execute("--run", "some_path")
        expected_path = "some_path"
        expected_pred_fields_storage = str(tests_command.DEFAULT_PREDEFINED_FIELDS_STORAGE)
        expected_make_csv = False
        tests_command.run_scenario_tests.assert_called_once_with(expected_path, expected_pred_fields_storage,
                                                                 expected_make_csv)
        tests_command.run_ssml_tests.assert_called_once_with()

    async def test_run_path(self):
        app_config = Mock(SSML_TEST_ADDRESS="")
        tests_command = TestsCommand(app_config)
        tests_command.run_scenario_tests = Mock(return_value=True)
        tests_command.run_ssml_tests = Mock(return_value=True)
        tests_command.execute("--run", "some_path")
        expected_path = "some_path"
        expected_pred_fields_storage = str(tests_command.DEFAULT_PREDEFINED_FIELDS_STORAGE)
        expected_make_csv = False
        tests_command.run_scenario_tests.assert_called_once_with(expected_path, expected_pred_fields_storage,
                                                                 expected_make_csv)
        tests_command.run_ssml_tests.assert_called_once_with()

    async def test_run_path_pfs(self):
        app_config = Mock(SSML_TEST_ADDRESS="")
        tests_command = TestsCommand(app_config)
        tests_command.run_scenario_tests = Mock(return_value=True)
        tests_command.run_ssml_tests = Mock(return_value=True)
        tests_command.execute("--run", "some_path", "pfs")
        expected_path = "some_path"
        expected_pred_fields_storage = "pfs"
        expected_make_csv = False
        tests_command.run_scenario_tests.assert_called_once_with(expected_path, expected_pred_fields_storage,
                                                                 expected_make_csv)
        tests_command.run_ssml_tests.assert_called_once_with()

    async def test_run_path_ssml_off(self):
        app_config = Mock(SSML_TEST_ADDRESS="")
        tests_command = TestsCommand(app_config)
        tests_command.run_scenario_tests = Mock(return_value=True)
        tests_command.run_ssml_tests = Mock(return_value=True)
        tests_command.execute("--run", "--ssml-off", "some_path")
        expected_path = "some_path"
        expected_pred_fields_storage = str(tests_command.DEFAULT_PREDEFINED_FIELDS_STORAGE)
        expected_make_csv = False
        tests_command.run_scenario_tests.assert_called_once_with(expected_path, expected_pred_fields_storage,
                                                                 expected_make_csv)
        tests_command.run_ssml_tests.assert_not_called()

    async def test_run_scen_off(self):
        app_config = Mock(SSML_TEST_ADDRESS="")
        tests_command = TestsCommand(app_config)
        tests_command.run_scenario_tests = Mock(return_value=True)
        tests_command.run_ssml_tests = Mock(return_value=True)
        tests_command.execute("--run", "--scenarios-off")
        tests_command.run_scenario_tests.assert_not_called()
        tests_command.run_ssml_tests.assert_called_with()

    async def test_run_ssml_interactive(self):
        app_config = Mock(SSML_TEST_ADDRESS="")
        tests_command = TestsCommand(app_config)
        tests_command.run_scenario_tests = Mock(return_value=True)
        tests_command.run_ssml_tests = Mock(return_value=True)
        tests_command.ssml_suite.test_single_string = Mock()
        with unittest.mock.patch('builtins.input') as inp:
            inputs = iter(["<speak>a</speak>", "a", ""])
            is_none = Mock()
            is_none.__bool__ = lambda *args: next(inputs) != ""
            inp.return_value = is_none
            tests_command.execute("--run", "--ssml-interactive")
        tests_command.run_scenario_tests.assert_not_called()
        tests_command.run_ssml_tests.assert_not_called()
        self.assertEqual(tests_command.ssml_suite.test_single_string.call_count, 2)

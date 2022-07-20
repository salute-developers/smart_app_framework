import argparse
import logging.config
from collections import namedtuple

from smart_kit.configs.logger_config import LOGGING_CONFIG
from smart_kit.configs.logger_config import LoggerConfig
from smart_kit.management.base import HelpCommand
from smart_kit.management.cache import CreateCacheCommand
from smart_kit.management.tests import TestsCommand
from smart_kit.management.plugins import activate_plugins
from smart_kit.start_points.app import run as app_runner
from smart_kit.management.get_bundles_from_pps import GetBundleCommand
from smart_kit.testing.ssml_test.suite import SsmlTestSuite


def init_logger(app_config):
    logger_config = LoggerConfig(app_config.CONFIGS_PATH)
    logger_config.init()
    config = logger_config[LOGGING_CONFIG]
    logging.log_store_for_map = config.get('log_store_for_map', None)
    logging.config.dictConfig(config)


class AppCommand:
    @classmethod
    def doc(cls):
        return cls.__doc__ or "No help provided"

    def execute(self, *args, **kwargs):
        raise NotImplementedError


class LocalTestingCommand(AppCommand):
    def __init__(self, app_config):
        self.app_config = app_config
        self._local_testing_wrapper = app_config.LOCAL_TESTING(
            configs_path=app_config.CONFIGS_PATH, secret_path=app_config.SECRET_PATH,
            settings_cls=app_config.SETTINGS, references_path=app_config.REFERENCES_PATH,
            resources_cls=app_config.RESOURCES, model_cls=app_config.MODEL, test_case_cls=app_config.TEST_CASE,
            dialogue_manager_cls=app_config.DIALOGUE_MANAGER, user_cls=app_config.USER,
            parametrizer_cls=app_config.PARAMETRIZER, from_msg_cls=app_config.FROM_MSG, app_name=app_config.APP_NAME
        )

    def execute(self, *args, **kwargs):
        init_logger(self.app_config)
        if self.app_config.NORMALIZER:
            self.app_config.NORMALIZER.load_everything()
        return self._local_testing_wrapper.run_local_testing(*args, **kwargs)


class RunAppCommand(AppCommand):
    def __init__(self, app_config):
        self.app_config = app_config
        self._runner = app_runner

    def execute(self, *args, **kwargs):
        init_logger(self.app_config)
        if self.app_config.NORMALIZER:
            self.app_config.NORMALIZER.load_everything()
        return self._runner(self.app_config)


class SsmlTestCommand(AppCommand):
    """Command for testing ssml strings"""
    def __init__(self, app_config):
        self.app_config = app_config
        self.parser = argparse.ArgumentParser(description="SSML strings testing.")
        self.commands = self.parser.add_mutually_exclusive_group(required=True)
        self.commands.add_argument("--statics", dest="statics", help="Test ssml strings in statics", action="store_true")
        self.commands.add_argument(
            "--string", dest="string", type=str, help="Test given ssml strings", action="store"
        )
        self.test_suite: SsmlTestSuite = app_config.SSML_TEST_SUITE(app_config.SSML_TEST_ADDRESS)

    def execute(self, *args, **kwargs):
        init_logger(self.app_config)
        namespace = self.parser.parse_args(args)
        print(namespace.string)
        if namespace.statics:
            self.test_statics()
        elif namespace.string is not None:
            self.test_single_string(namespace.string)

    def test_statics(self):
        settings = self.app_config.SETTINGS(
            config_path=self.app_config.CONFIGS_PATH, secret_path=self.app_config.SECRET_PATH,
            references_path=self.app_config.REFERENCES_PATH, app_name=self.app_config.APP_NAME)
        source = settings.get_source()
        resources = self.app_config.RESOURCES(source, self.app_config.REFERENCES_PATH, settings)
        resource_to_ssml_string_parser = self.app_config.RESOURCE_TO_SSML_STRING_PARSER
        self.test_suite.test_statics(resources, resource_to_ssml_string_parser)

    def test_single_string(self, string_to_test: str):
        self.test_suite.test_single_string(string_to_test)


class AppManager:
    def __init__(self):
        self.commands = {}
        self.Command = namedtuple('Command', 'command_class args kwargs')

    def register_command(self, name, command, *args, **kwargs):
        self.commands[name] = self.Command(command, args, kwargs)

    def execute_command(self, name, *args, **kwargs):
        current_command = self.commands[name]
        command = current_command.command_class(*current_command.args, **current_command.kwargs)
        return command.execute(*args, **kwargs)

    def execute_from_command_line(self, argv):
        if len(argv) == 1:
            name = "help"
        else:
            name = argv[1]

        return self.execute_command(name, *argv[2:])


def execute_from_command_line(argv):
    from smart_kit.configs import get_app_config
    app_config = get_app_config()
    manager = AppManager()
    manager.register_command("local_testing", LocalTestingCommand, app_config)
    manager.register_command("run_app", RunAppCommand, app_config)
    manager.register_command("tests", TestsCommand, app_config)
    manager.register_command("cache", CreateCacheCommand, app_config)
    manager.register_command("help", HelpCommand, manager.commands)
    manager.register_command("get_bundles", GetBundleCommand, app_config)
    manager.register_command("ssml_test", SsmlTestCommand, app_config)

    activate_plugins(app_config, manager)

    return manager.execute_from_command_line(argv)

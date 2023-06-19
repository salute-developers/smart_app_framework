import logging.config

from smart_kit.configs.logger_config import LOGGING_CONFIG
from smart_kit.configs.logger_config import LoggerConfig


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


class HelpCommand(AppCommand):
    def __init__(self, commands):
        self._commands = commands

    def execute(self, *args, **kwargs):
        if not args:
            print("Available commands:")
            for cmd in self._commands:
                print(f"\t {cmd}")
            return
        if len(args) >= 2:
            raise ValueError("Wrong command usage")

        name = args[0]
        if name not in self._commands:
            print(f"{name} command not registered")
            return

        command = self._commands[name]
        print(command.doc())


class Manager:
    def __init__(self):
        self.commands = {}

    def register_command(self, name, command, *args, **kwargs):
        self.commands[name] = command(*args, **kwargs)

    def execute_command(self, name, *args, **kwargs):
        return self.commands[name].execute(*args, **kwargs)

    def default(self, argv):
        return NotImplementedError

    def execute_from_command_line(self, argv):
        if len(argv) <= 1:
            return self.default(argv)

        name = argv[1]

        if name not in self.commands:
            return self.default(argv)

        return self.execute_command(name, *argv[2:])

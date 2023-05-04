# coding: utf-8
import os

import yaml

from core.configs.base_config import BaseConfig
from core.repositories.file_repository import FileRepository
from core.utils.version import get_nlpf_version
from smart_kit.utils.logger_writer.logger_formatter import SmartKitJsonFormatter


def setup_version():
    SmartKitJsonFormatter.NLPF_VERSION = get_nlpf_version() or 0
    SmartKitJsonFormatter.VERSION = os.getenv("VERSION") or 0


setup_version()


LOGGING_CONFIG = "logging_config"


class LoggerConfig(BaseConfig):
    def __init__(self, config_path):
        self.config_path = config_path
        super(LoggerConfig, self).__init__()
        self.repositories = [
            FileRepository(self.subfolder_path("logging_config.yml"),
                           loader=yaml.safe_load, key=LOGGING_CONFIG)
        ]

    @property
    def _subfolder(self):
        return self.config_path

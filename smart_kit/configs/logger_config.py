# coding: utf-8
import os
from typing import Optional

import pkg_resources
import yaml

from core.configs.base_config import BaseConfig
from core.repositories.file_repository import FileRepository
from smart_kit.utils.logger_writer.logger_formatter import SmartKitJsonFormatter


def _get_distribution_safe(name: str) -> Optional[pkg_resources.DistInfoDistribution]:
    try:
        distribution = pkg_resources.get_distribution(name)
        return distribution
    except pkg_resources.DistributionNotFound:
        return None


def setup_version():
    version = os.getenv("VERSION")
    if version is None:
        distribution = _get_distribution_safe("sber-nlp-platform-smart-app-framework")
        if distribution is None:
            distribution = _get_distribution_safe("smart-app-framework")
        version = distribution.version if distribution is not None else 0

    SmartKitJsonFormatter.VERSION = version


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

"""
# Допустимые форматы файлов для StaticStorage.
"""

from .smart_enum import SmartEnum


class FileFormat(SmartEnum):
    """
    # Допустимые форматы файлов для StaticStorage.
    """

    YAML = "yaml"
    JSON = "json"

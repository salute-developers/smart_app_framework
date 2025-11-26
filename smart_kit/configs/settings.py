from __future__ import annotations

import asyncio
import os
from io import StringIO
from typing import Any, Union, List, Optional

import yaml

from core.configs.base_config import BaseConfig
from core.db_adapter.ceph.ceph_adapter import CephAdapter
from core.db_adapter.db_adapter import DBAdapter
from core.db_adapter.os_adapter import OSAdapter
from core.repositories.file_repository import UpdatableFileRepository, FileRepository
from core.repositories.secret_file_repository import SecretUpdatableFileRepository
from core.utils.singleton import SingletonOneInstance
from smart_kit.configs import get_app_config


class Version:
    def __init__(self, code_version: Optional[str], separate_static=False, static_version: Optional[str] = None):
        self.code_version = code_version
        self.separate_static = separate_static
        self.static_version = static_version

    def __str__(self):
        if self.separate_static:
            return f"Версия кода: {self.code_version or 'UNKNOWN'}; Версия статиков: {self.static_version or 'UNKNOWN'}"
        return self.code_version or "UNKNOWN"

    @classmethod
    def from_env_and_source(cls, source: DBAdapter) -> "Version":
        code_version = os.getenv("VERSION", default=0)
        attrs = {"code_version": code_version}
        if isinstance(source, CephAdapter):
            attrs["separate_static"] = True
            try:
                static_version = cls._get_version_from_ceph(source)
                attrs["static_version"] = static_version
            except FileNotFoundError:
                pass
        return cls(**attrs)

    @staticmethod
    def _get_version_from_ceph(source: CephAdapter) -> str:
        path = os.path.join(get_app_config().REFERENCES_PATH, "BUILD.txt")
        if not source.path_exists(path):
            raise FileNotFoundError(f"{path} file not found in ceph")
        with source.open(path, "r") as f:
            f: StringIO
            version = f.readline()
        return version


class Settings(BaseConfig, metaclass=SingletonOneInstance):
    CephAdapterKey = "ceph"
    OSAdapterKey = "os"

    def __init__(self, *args, **kwargs):
        super().__init__()
        self.configs_path = kwargs.get("config_path")
        self.references_path = kwargs.get("references_path")
        self.secret_path = kwargs.get("secret_path")
        self.app_name = kwargs.get("app_name")
        self.adapters = {Settings.CephAdapterKey: CephAdapter, self.OSAdapterKey: OSAdapter}
        self.loop = asyncio.get_event_loop()
        self.repositories = self._load_base_repositories()
        self.repositories = self.override_repositories(self.repositories)
        self.init()
        self.version = Version.from_env_and_source(self.get_source())

    def init(self):
        super().init()
        update_time = self["template_settings"].get("config_update_cooldown")
        if update_time is not None:
            for repo in self.repositories:
                if isinstance(repo, UpdatableFileRepository):
                    repo.update_cooldown = update_time

    def override_repositories(self, repositories: List):
        """
        Метод предназначен для переопределения репозиториев в дочерних классах.
        :param repositories: Список репозиториев родителя
        :return: Переопределённый в наследниках список репозиториев
        """
        return repositories

    def _load_base_repositories(self) -> List[FileRepository]:
        """Load base repositories with service settings"""
        template_settings_repo = SecretUpdatableFileRepository(
            filename=self.subfolder_path("template_config.yml"),
            secret_filename=self.subfolder_secret_path("template_config.yml"),
            loader=yaml.safe_load,
            key="template_settings")
        template_settings_repo.load()

        use_secrets_path_for_kafka: bool = template_settings_repo.data.get("kafka_use_secrets_path", True)
        kafka_config_repo = FileRepository(
            self._get_kafka_settings_filepath("kafka_config.yml", use_secrets_path=use_secrets_path_for_kafka),
            loader=yaml.safe_load, key="kafka")

        ceph_config_repo = FileRepository(
            self.subfolder_path("ceph_config.yml"), loader=yaml.safe_load, key=self.CephAdapterKey)

        aiohttp_config_repo = FileRepository(self.subfolder_path("aiohttp.yml"), loader=yaml.safe_load, key="aiohttp")

        return [
            template_settings_repo,
            kafka_config_repo,
            ceph_config_repo,
            aiohttp_config_repo,
        ]

    def _get_kafka_settings_filepath(
            self, filename: Any, use_secrets_path: bool = True) -> Union[bytes, str]:
        """Возвращает путь к файлу с настройками кафки. По умолчанию возвращает путь к файлу в секретах."""
        if use_secrets_path:
            return self.subfolder_secret_path(filename)
        return self.subfolder_path(filename)

    @property
    def _subfolder(self):
        return self.configs_path

    def subfolder_secret_path(self, filename):
        return os.path.join(self.secret_path, filename)

    def get_source(self):
        if hasattr(self, "_source"):
            return self._source

        adapter_key = self.registered_repositories["template_settings"].data.get(
            "data_adapter") or Settings.OSAdapterKey
        adapter_settings = self.registered_repositories[
            adapter_key].data if adapter_key != Settings.OSAdapterKey else None
        adapter = self.adapters[adapter_key](adapter_settings)
        if asyncio.iscoroutinefunction(adapter.connect):
            self.loop.run_until_complete(adapter.connect())
        else:
            adapter.connect()
        source = adapter.source

        self._source = source
        return source

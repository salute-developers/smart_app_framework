from __future__ import annotations

import asyncio
import os
from typing import Optional, Any, Union, List

import yaml

from core.configs.base_config import BaseConfig
from core.db_adapter.ceph.ceph_adapter import CephAdapter
from core.db_adapter.os_adapter import OSAdapter
from core.repositories.file_repository import UpdatableFileRepository, FileRepository
from core.utils.singleton import SingletonOneInstance


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

    def init(self):
        super().init()
        update_time = self["template_settings"].get("config_update_cooldown")
        if update_time is not None:
            for repo in self.repositories:
                if isinstance(repo, UpdatableFileRepository):
                    repo.update_cooldown = update_time

    def override_repositories(self, repositories: list):
        """
        Метод предназначен для переопределения репозиториев в дочерних классах.
        :param repositories: Список репозиториев родителя
        :return: Переопределённый в наследниках список репозиториев
        """
        return repositories

    def _load_base_repositories(self) -> List[FileRepository]:
        """Load base repositories with service settings"""
        template_settings_repo = UpdatableFileRepository(
            self.subfolder_path("template_config.yml"), loader=yaml.safe_load, key="template_settings")
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

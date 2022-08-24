# coding: utf-8
from typing import Dict, Callable, Any

from core.descriptions.descriptions_items import DescriptionsItems
from core.model.registered import Registered
from core.repositories.base_repository import BaseRepository

registered_description_factories = Registered()


def default_description_factory(x):
    return x


class Descriptions:
    def __init__(self, registered_repositories: Dict[str, BaseRepository]) -> None:
        self.registered_repositories: Dict[str, BaseRepository] = registered_repositories
        self._descriptions: dict = {}

    def __getitem__(self, key: str) -> Any:
        description_item = self._descriptions.get(key)
        if description_item is None:
            repository: BaseRepository = self.registered_repositories[key]
            factory: Callable = registered_description_factories.get(key, default_description_factory)
            description_item = factory(repository.data)
            self._descriptions[key] = description_item
        return description_item

    def __setitem__(self, key: str, description_item: DescriptionsItems) -> None:
        self._descriptions[key] = description_item

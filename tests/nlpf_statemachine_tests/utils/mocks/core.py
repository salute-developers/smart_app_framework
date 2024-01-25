"""
# Генерация базовых объектов NLPF.
"""
import os
from copy import deepcopy

from lazy import lazy

from core.descriptions.descriptions import Descriptions
from nlpf_statemachine.config import CONTEXT_MANAGER_ID, STATE_MACHINE_REPOSITORY_NAME
from nlpf_statemachine.kit import ContextManager
from nlpf_statemachine.override import SMDialogueManager, SMSmartAppModel, SMSmartAppResources
from smart_kit.configs import get_app_config
from smart_kit.configs.settings import Settings


class TestsCore:
    """
    # Генерация базовых объектов NLPF.
    """

    def __init__(self, smart_kit_app_config: str) -> None:
        os.environ["SMART_KIT_APP_CONFIG"] = smart_kit_app_config
        self.app_config = get_app_config()

    @lazy
    def settings(self) -> Settings:
        """## Генерация объекта Settings."""
        return self.app_config.SETTINGS(
            config_path=self.app_config.CONFIGS_PATH,
            secret_path=self.app_config.SECRET_PATH,
            references_path=self.app_config.REFERENCES_PATH,
            app_name=self.app_config.APP_NAME,
        )

    @lazy
    def resources(self) -> SMSmartAppResources:
        """## Генерация объекта SmartAppResources."""
        return self.app_config.RESOURCES(
            source=self.settings.get_source(),
            references_path=self.app_config.REFERENCES_PATH,
            settings=self.settings,
        )

    @lazy
    def context_manager(self) -> ContextManager:
        """## Генерация объекта ContextManager."""
        repository = self.resources.registered_repositories.get(
            STATE_MACHINE_REPOSITORY_NAME, None,
        )
        return deepcopy(repository.data.get(CONTEXT_MANAGER_ID, None))

    @lazy
    def descriptions(self) -> Descriptions:
        """## Генерация объекта Descriptions."""
        return Descriptions(registered_repositories=self.resources.registered_repositories)

    @lazy
    def dialogue_manager(self) -> SMDialogueManager:
        """## Генерация объекта DialogueManager."""
        return SMDialogueManager(
            app_name=self.app_config.APP_NAME,
            scenario_descriptions=self.descriptions,
        )

    @lazy
    def smart_app_model(self) -> SMSmartAppModel:
        """## Генерация объекта SmartAppModel."""
        return SMSmartAppModel(
            resources=self.resources,
            dialogue_manager_cls=SMDialogueManager,
            custom_settings=self.settings,
        )

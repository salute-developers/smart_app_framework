import os

from nlpf_statemachine.const import CONTEXT_MANAGER_ID, STATE_MACHINE_REPOSITORY_NAME
from nlpf_statemachine.kit.test_utils.utils import TestUtils as TestUtilsBase
from nlpf_statemachine.models import Context
from smart_kit.configs import get_app_config


class TestUtils(TestUtilsBase):
    CONTEXT_CLASS = Context
    SMART_KIT_APP_CONFIG = "app_config"

    def setUp(self) -> None:
        super().setUp()
        self.context_manager = self._get_context_manager()

    def _get_context_manager(self) -> None:
        os.environ["SMART_KIT_APP_CONFIG"] = self.SMART_KIT_APP_CONFIG
        self.app_config = get_app_config()
        settings = self.app_config.SETTINGS(
            config_path=self.app_config.CONFIGS_PATH,
            secret_path=self.app_config.SECRET_PATH,
            references_path=self.app_config.REFERENCES_PATH,
            app_name=self.app_config.APP_NAME,
        )
        source = settings.get_source()
        resource = self.app_config.RESOURCES(
            source, self.app_config.REFERENCES_PATH, settings,
        )
        repository = resource.registered_repositories.get(
            STATE_MACHINE_REPOSITORY_NAME, None,
        )
        return repository.data.get(CONTEXT_MANAGER_ID, None)

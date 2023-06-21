from core.basic_models.requirement.basic_requirements import requirements
from core.basic_models.actions.basic_actions import actions
from core.db_adapter.db_adapter import db_adapters
import scenarios.scenario_models.field.field_filler_description as ffd
from smart_kit.resources import SmartAppResources

from app.adapters.db_adapters import CustomDBAdapter
from app.basic_entities.actions import CustomAction
from app.basic_entities.fillers import CustomFieldFiller
from app.basic_entities.requirements import CustomRequirement


class CustomAppResources(SmartAppResources):
    """Класс инициализирует репозитории элементов языка фреймворка, то есть сопоставляет Python-классы именам языка

    Для использования данных ресурсов присвойте переменной RESOURCES в app_config этот класс как значение.
    """
    def override_repositories(self, repositories: list):
        """Метод предназначен для переопределения репозиториев в дочерних классах

        :param repositories: Список репозиториев родителя
        :return: Переопределённый в наследниках список репозиториев
        """
        return repositories

    def init_field_filler_description(self):
        super().init_field_filler_description()
        ffd.field_filler_description["custom_filler"] = CustomFieldFiller

    def init_actions(self):
        super().init_actions()
        actions["custom_action"] = CustomAction

    def init_requirements(self):
        super().init_requirements()
        requirements["custom_requirement"] = CustomRequirement

    def init_db_adapters(self):
        super().init_db_adapters()
        db_adapters["custom_db_adapter"] = CustomDBAdapter

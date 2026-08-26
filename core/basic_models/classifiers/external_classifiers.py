from typing import Any

from core.basic_models.classifiers.basic_classifiers import classifier_factory
from core.descriptions.smart_updatable_descriptions_items import SmartUpdatableDescriptionsItems


class ExternalClassifiers(SmartUpdatableDescriptionsItems):

    def __init__(self, settings: dict[str, Any]) -> None:
        super().__init__(classifier_factory, settings, ordered=True)

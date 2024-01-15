from typing import List

from core.message.validators.base_validator import BaseMessageValidator
from smart_kit.configs.settings import Settings
from smart_kit.models.smartapp_model import SmartAppModel
from smart_kit.utils.dynamic_import import dynamic_import_object


def get_validators_from_settings(validator_group: str, settings: Settings, model: SmartAppModel) \
        -> List[BaseMessageValidator]:
    validators = settings["template_settings"].get("validators", {})
    return [dynamic_import_object(e["class"])(resources=model.resources, **e["params"])
            for e in validators.get(validator_group, [])]

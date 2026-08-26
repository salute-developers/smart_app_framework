from core.descriptions.smart_updatable_descriptions_items import SmartUpdatableDescriptionsItems
from scenarios.scenario_models.forms.form_description import form_description_factory


class FormsDescription(SmartUpdatableDescriptionsItems):
    def __init__(self, items):
        super().__init__(form_description_factory, items)

from core.descriptions.smart_updatable_descriptions_items import SmartUpdatableDescriptionsItems
from scenarios.behaviors.behavior_description import BehaviorDescription


class BehaviorDescriptions(SmartUpdatableDescriptionsItems):
    def __init__(self, items):
        super().__init__(BehaviorDescription, items)

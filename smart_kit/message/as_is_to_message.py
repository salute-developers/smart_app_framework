from functools import cached_property

from core.message.from_message import SmartAppFromMessage
from smart_kit.message.smartapp_to_message import SmartAppToMessage


class AsIsToMessage(SmartAppToMessage):

    @cached_property
    def as_dict(self):
        self.incoming_message: SmartAppFromMessage
        fields = self.command.raw
        fields.update(self.root_nodes)
        return fields

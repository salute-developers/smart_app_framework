"""
# Описание протокола запросов в смартап.

[Подробнее тут.](https://developers.sber.ru/docs/ru/salute/api/smartapp_api_requests)
"""
from .annotations import Annotations, AnnotationsDetails
from .app_info import AppInfo
from .assistant_message import AssistantMessage
from .base_message import BaseMessage
from .character import Character
from .current_app import AssistantState, CurrentApp
from .device import Device
from .device_capability import DeviceCapabilities, DeviceCapability
from .device_features import DeviceFeatures
from .feature_launcher import FeatureLauncher, PublicFL
from .item_selector import AssistantViewAction, AssistantVoiceAction, ItemSelector
from .message_object import Message
from .meta import AssistantMeta, MetaFeature, MetaFeatures, MetaTime
from .payload import AssistantPayload, MessageToSkillPayload, ServerActionPayload
from .request_data import RequestData
from .selected_item import SelectedItem
from .server_action import ServerAction
from .stratagies import Strategies
from .uuid import UUID

__all__ = [
    Annotations,
    AnnotationsDetails,
    AppInfo,
    AssistantMessage,
    AssistantMeta,
    AssistantPayload,
    AssistantState,
    AssistantViewAction,
    AssistantVoiceAction,
    BaseMessage,
    Character,
    CurrentApp,
    Device,
    DeviceCapabilities,
    DeviceCapability,
    DeviceFeatures,
    FeatureLauncher,
    ItemSelector,
    Message,
    MessageToSkillPayload,
    MetaFeature,
    MetaFeatures,
    MetaTime,
    PublicFL,
    RequestData,
    SelectedItem,
    ServerAction,
    ServerActionPayload,
    Strategies,
    UUID,
]

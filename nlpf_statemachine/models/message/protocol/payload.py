"""
# Описание Payload для основных запросов.
"""

from typing import Any, Dict, Optional, List

from pydantic import BaseModel

from .annotations import Annotations
from .app_info import AppInfo
from .character import Character
from .device import Device
from .feature_launcher import FeatureLauncher
from .message_object import Message
from .meta import AssistantMeta
from .selected_item import SelectedItem
from .server_action import ServerAction
from .stratagies import Strategies


class AssistantPayload(BaseModel):
    """
    # Описание модели AssistantPayload.
    """

    app_info: Optional[AppInfo]
    """Информация о смартапе."""
    intent: Optional[str]
    """Интент, полученный из предыдущего ответа смартапа"""
    original_intent: Optional[str]
    """Исходный интент. Значение поля отличается от значения intent только при монопольном захвате контекста"""
    meta: Optional[AssistantMeta]
    """Данные о содержимом экрана пользователя."""
    projectName: Optional[str]
    """Имя смартапа, которое задается при создании проекта и отображается в каталоге приложений."""
    device: Optional[Device]
    """Информация об устройстве пользователя."""
    new_session: Optional[bool]
    """
    Указывает на характер запуска смартапа.

    Если поле содержит true, сессии присваивается новый идентификатор (поле sessionId).
    Возможные значения:

    * `true` — приложение запущено впервые или после закрытия приложения,
      а также при запуске приложения по истечению тайм-аута (10 минут)
      или после прерывания работы приложения, например, по запросу "текущее время";
    * `false` — во всех остальных случаях.

    По умолчанию: `false`.
    """
    character: Optional[Character]
    """Информация о текущем персонаже ассистента, который установлен у пользователя."""
    strategies: Optional[Strategies]
    """Возможные стратегии смартапа."""
    smartBio: Optional[Dict[str, Any]]
    """Данные от биометрии"""
    contentProvider: Optional[Dict[str, Any]]
    """Проброс payload для звонков вк"""
    epkId: Optional[str]
    """ЕПК ID"""
    ufs_info: Optional[Dict[str, Any]]
    """Блок с куками для ЕФС"""
    applicationId: Optional[str]
    """Id апликейшена проекта из апп дир"""
    appversionId: Optional[str]
    """Id версии проекта из апп дир"""
    token: Optional[str]
    """Токен поверхности"""
    tokenType: Optional[str]
    """Тип токена"""
    client_profile: Optional[Dict[str, Any]]
    """
    Передается во внутренние аппы и в Axon, если DP удалось получить профиль.
    Профиль обновляется не каждый запрос а N раз в день. Профиль - ЕПК.
    """
    feature_launcher: Optional[FeatureLauncher]
    """Коллекция флагов для проведения экспериментов для сервисов и навыков Виртуального Ассистента"""
    reverseGeocoding: Optional[Dict[str, Any]]
    """Данные от сервиса геокодинга"""
    legacyEribInfo: Optional[Dict[str, Any]]
    """Поддержка токена ЕРИБ"""
    dynamic_stuff: Optional[Dict[str, Any]]
    """Динамические данные"""
    backInfo: Optional[List]
    """Данные для доступа к брокерским счетам"""
    permitted_actions: Optional[List]
    """Список согласий этого пользователя которые он дал этому навыку"""
    additional_info: Optional[Dict[str, Any]]
    """Дополнительные данные для запуска приложения"""
    domain_search: Optional[Dict]
    """Результат поиска сущностей по домену"""
    linkedSmartapp: Optional[Dict]
    """Информация о навыке, который запускает прилинкованный навык в случае если исходный навык недоступен"""
    last_messages_new: Optional[Dict]
    """N последних сообщениq от пользователя + интент + ответы ассистента для аксон"""
    last_messages: Optional[Dict]
    """N последних сообщениq от пользователя + интент + ответы ассистента"""
    dp_first_session: Optional[bool]
    """
    Флаг, говорящий, является ли это самой первой сессией общения с пользователем
    Передается только в навыки "приветствий"
    """
    is_first_session: Optional[bool]
    """Флаг первой сессии из VPS. Передается только в навыки "приветствий" """
    employeeId: Optional[str]
    """Идентификатор сотрудника. Передается только для внутренних навыков"""
    employee_profile: Optional[Dict]
    """Профиль сотрудника. Передается только для внутренних навыков и только в канале B2E"""
    debug_info: Optional[Dict]
    """Дебаг информация по сервисам"""


class ServerActionPayload(AssistantPayload):
    """
    # Payload для SERVER_ACTION.
    """

    server_action: ServerAction
    """Описание команды для бэкенда смартапа."""


class MessageToSkillPayload(AssistantPayload):
    """
    # Payload для MESSAGE_TO_SKILL + CLOSE_APP.
    """

    message: Message
    """Результат предобработки сообщения."""
    intent_meta: Optional[Dict]
    """
    Мета данные, полученные от сервиса распознавания интентов.
    Поле будет использовано в будущем. В текущей реализации содержит пустой объект.
    """
    selected_item: Optional[SelectedItem]
    """Описание элемента экрана, который пользователь назвал при запросе."""
    annotations: Optional[Annotations]
    """Общие характеристики сообщения пользователя."""
    asr: Optional[Dict[str, Any]]
    """Блок с гипотезами от ASR."""

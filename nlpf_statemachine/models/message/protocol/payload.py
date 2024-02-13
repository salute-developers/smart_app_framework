"""
# Описание Payload для основных запросов.
"""

from typing import Optional, List, Dict

from pydantic import BaseModel, Field

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

    app_info: Optional[AppInfo] = Field(default=None)
    """Информация о смартапе."""
    intent: Optional[str] = Field(default=None)
    """Интент, полученный из предыдущего ответа смартапа"""
    original_intent: Optional[str] = Field(default=None)
    """Исходный интент. Значение поля отличается от значения intent только при монопольном захвате контекста"""
    meta: AssistantMeta = Field(default_factory=AssistantMeta)
    """Данные о содержимом экрана пользователя."""
    projectName: Optional[str] = Field(default=None)
    """Имя смартапа, которое задается при создании проекта и отображается в каталоге приложений."""
    device: Optional[Device] = Field(default=None)
    """Информация об устройстве пользователя."""
    new_session: Optional[bool] = Field(default=None)
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
    character: Optional[Character] = Field(default=None)
    """Информация о текущем персонаже ассистента, который установлен у пользователя."""
    strategies: Optional[Strategies] = Field(default=None)
    """Возможные стратегии смартапа."""
    smartBio: Optional[Dict] = Field(default=None)
    """Данные от биометрии"""
    contentProvider: Optional[Dict] = Field(default=None)
    """Проброс payload для звонков вк"""
    epkId: Optional[str] = Field(default=None)
    """ЕПК ID"""
    ufs_info: Optional[Dict] = Field(default=None)
    """Блок с куками для ЕФС"""
    applicationId: Optional[str] = Field(default=None)
    """Id апликейшена проекта из апп дир"""
    appversionId: Optional[str] = Field(default=None)
    """Id версии проекта из апп дир"""
    token: Optional[str] = Field(default=None)
    """Токен поверхности"""
    tokenType: Optional[str] = Field(default=None)
    """Тип токена"""
    client_profile: Optional[Dict] = Field(default=None)
    """
    Передается во внутренние аппы и в Axon, если DP удалось получить профиль.
    Профиль обновляется не каждый запрос а N раз в день. Профиль - ЕПК.
    """
    feature_launcher: Optional[FeatureLauncher] = Field(default=None)
    """Коллекция флагов для проведения экспериментов для сервисов и навыков Виртуального Ассистента"""
    reverseGeocoding: Optional[Dict] = Field(default=None)
    """Данные от сервиса геокодинга"""
    legacyEribInfo: Optional[Dict] = Field(default=None)
    """Поддержка токена ЕРИБ"""
    dynamic_stuff: Optional[Dict] = Field(default=None)
    """Динамические данные"""
    backInfo: Optional[List] = Field(default=None)
    """Данные для доступа к брокерским счетам"""
    permitted_actions: Optional[List] = Field(default=None)
    """Список согласий этого пользователя которые он дал этому навыку"""
    additional_info: Optional[Dict] = Field(default=None)
    """Дополнительные данные для запуска приложения"""
    domain_search: Optional[Dict] = Field(default=None)
    """Результат поиска сущностей по домену"""
    linkedSmartapp: Optional[Dict] = Field(default=None)
    """Информация о навыке, который запускает прилинкованный навык в случае если исходный навык недоступен"""
    last_messages_new: Optional[Dict] = Field(default=None)
    """N последних сообщениq от пользователя + интент + ответы ассистента для аксон"""
    last_messages: Optional[Dict] = Field(default=None)
    """N последних сообщениq от пользователя + интент + ответы ассистента"""
    dp_first_session: Optional[bool] = Field(default=None)
    """
    Флаг, говорящий, является ли это самой первой сессией общения с пользователем
    Передается только в навыки "приветствий"
    """
    is_first_session: Optional[bool] = Field(default=None)
    """Флаг первой сессии из VPS. Передается только в навыки "приветствий" """
    employeeId: Optional[str] = Field(default=None)
    """Идентификатор сотрудника. Передается только для внутренних навыков"""
    employee_profile: Optional[Dict] = Field(default=None)
    """Профиль сотрудника. Передается только для внутренних навыков и только в канале B2E"""
    debug_info: Optional[Dict] = Field(default=None)
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
    intent_meta: Optional[Dict] = Field(default=None)
    """
    Мета данные, полученные от сервиса распознавания интентов.
    Поле будет использовано в будущем. В текущей реализации содержит пустой объект.
    """
    selected_item: Optional[SelectedItem] = Field(default=None)
    """Описание элемента экрана, который пользователь назвал при запросе."""
    annotations: Optional[Annotations] = Field(default=None)
    """Общие характеристики сообщения пользователя."""
    asr: Optional[str] = Field(default=None)
    """Блок с гипотезами от ASR."""

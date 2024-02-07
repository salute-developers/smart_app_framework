"""
# Описание Payload для основных запросов.
"""

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

    app_info: AppInfo | None = Field(default=None)
    """Информация о смартапе."""
    intent: str | None = Field(default=None)
    """Интент, полученный из предыдущего ответа смартапа"""
    original_intent: str | None = Field(default=None)
    """Исходный интент. Значение поля отличается от значения intent только при монопольном захвате контекста"""
    meta: AssistantMeta = Field(default_factory=AssistantMeta)
    """Данные о содержимом экрана пользователя."""
    projectName: str | None = Field(default=None)
    """Имя смартапа, которое задается при создании проекта и отображается в каталоге приложений."""
    device: Device | None = Field(default=None)
    """Информация об устройстве пользователя."""
    new_session: bool | None = Field(default=None)
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
    character: Character | None = Field(default=None)
    """Информация о текущем персонаже ассистента, который установлен у пользователя."""
    strategies: Strategies | None = Field(default=None)
    """Возможные стратегии смартапа."""
    smartBio: dict | None = Field(default=None)
    """Данные от биометрии"""
    contentProvider: dict | None = Field(default=None)
    """Проброс payload для звонков вк"""
    epkId: str | None = Field(default=None)
    """ЕПК ID"""
    ufs_info: dict | None = Field(default=None)
    """Блок с куками для ЕФС"""
    applicationId: str | None = Field(default=None)
    """Id апликейшена проекта из апп дир"""
    appversionId: str | None = Field(default=None)
    """Id версии проекта из апп дир"""
    token: str | None = Field(default=None)
    """Токен поверхности"""
    tokenType: str | None = Field(default=None)
    """Тип токена"""
    client_profile: dict | None = Field(default=None)
    """
    Передается во внутренние аппы и в Axon, если DP удалось получить профиль.
    Профиль обновляется не каждый запрос а N раз в день. Профиль - ЕПК.
    """
    feature_launcher: FeatureLauncher | None = Field(default=None)
    """Коллекция флагов для проведения экспериментов для сервисов и навыков Виртуального Ассистента"""
    reverseGeocoding: dict | None = Field(default=None)
    """Данные от сервиса геокодинга"""
    legacyEribInfo: dict | None = Field(default=None)
    """Поддержка токена ЕРИБ"""
    dynamic_stuff: dict | None = Field(default=None)
    """Динамические данные"""
    backInfo: list | None = Field(default=None)
    """Данные для доступа к брокерским счетам"""
    permitted_actions: list | None = Field(default=None)
    """Список согласий этого пользователя которые он дал этому навыку"""
    additional_info: dict | None = Field(default=None)
    """Дополнительные данные для запуска приложения"""
    domain_search: dict | None = Field(default=None)
    """Результат поиска сущностей по домену"""
    linkedSmartapp: dict | None = Field(default=None)
    """Информация о навыке, который запускает прилинкованный навык в случае если исходный навык недоступен"""
    last_messages_new: dict | None = Field(default=None)
    """N последних сообщениq от пользователя + интент + ответы ассистента для аксон"""
    last_messages: dict | None = Field(default=None)
    """N последних сообщениq от пользователя + интент + ответы ассистента"""
    dp_first_session: bool | None = Field(default=None)
    """
    Флаг, говорящий, является ли это самой первой сессией общения с пользователем
    Передается только в навыки "приветствий"
    """
    is_first_session: bool | None = Field(default=None)
    """Флаг первой сессии из VPS. Передается только в навыки "приветствий" """
    employeeId: str | None = Field(default=None)
    """Идентификатор сотрудника. Передается только для внутренних навыков"""
    employee_profile: dict | None = Field(default=None)
    """Профиль сотрудника. Передается только для внутренних навыков и только в канале B2E"""
    debug_info: dict | None = Field(default=None)
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
    intent_meta: dict | None = Field(default=None)
    """
    Мета данные, полученные от сервиса распознавания интентов.
    Поле будет использовано в будущем. В текущей реализации содержит пустой объект.
    """
    selected_item: SelectedItem | None = Field(default=None)
    """Описание элемента экрана, который пользователь назвал при запросе."""
    annotations: Annotations | None = Field(default=None)
    """Общие характеристики сообщения пользователя."""
    asr: str | None = Field(default=None)
    """Блок с гипотезами от ASR."""

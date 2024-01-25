"""
# Переопределение NLPF SmartAppModel и хэндлеров для разных типов сообщений.
"""
from typing import Any, List, Type

from core.basic_models.actions.command import Command
from core.monitoring.monitoring import monitoring
from core.text_preprocessing.preprocessing_result import TextPreprocessingResult
from nlpf_statemachine.const import DEFAULT, INTEGRATION_TIMEOUT
from nlpf_statemachine.models import Event, RequestMessageName
from nlpf_statemachine.override import SMDialogueManager
from smart_kit.handlers.handle_close_app import HandlerCloseApp
from smart_kit.handlers.handle_respond import HandlerRespond
from smart_kit.handlers.handle_server_action import HandlerServerAction
from smart_kit.handlers.handler_base import HandlerBase
from smart_kit.handlers.handler_text import HandlerText
from smart_kit.handlers.handler_timeout import HandlerTimeout
from smart_kit.models.smartapp_model import SmartAppModel
from smart_kit.resources import SmartAppResources
from .user import SMUser


class SMHandlerServerAction(HandlerServerAction):
    """
    # Переопределение обработчика для SERVER_ACTION.
    """

    def __init__(self, app_name: str, action_name: str = None, dialogue_manager: SMDialogueManager = None) -> None:
        super(SMHandlerServerAction, self).__init__(app_name=app_name, action_name=action_name)
        self.dialogue_manager = dialogue_manager

    async def run(self, payload: Any, user: SMUser) -> List[Command]:
        """
        ## Запуск обработчика.

        Args:
            payload: Payload.
            user (SMUser): Объект NLPF User.

        Returns:
            List[Command]
        """
        action_id = self.get_action_name(payload, user)
        answer = await self.dialogue_manager.run_statemachine(action_id, TextPreprocessingResult({}), user)
        if not answer:
            answer = await super(SMHandlerServerAction, self).run(payload=payload, user=user)
        else:
            monitoring.counter_incoming(
                self.app_name, user.message.message_name, self.__class__.__name__, user, app_info=user.message.app_info,
            )
        return answer


class SMRunAppHandler(HandlerText, HandlerServerAction):
    """
    # Переопределение обработчика для RUN_APP.
    """

    def __init__(self, app_name: str, action_name: str = None, dialogue_manager: SMDialogueManager = None) -> None:
        self.app_name = app_name
        self.action_name = action_name
        self.dialogue_manager = dialogue_manager

    async def run(self, payload: Any, user: SMUser) -> List[Command]:
        """
        ## Запуск обработчика.

        Args:
            payload: Payload.
            user (SMUser): Объект NLPF User.

        Returns:
            List[Command]
        """
        if payload.get("message"):
            event = None
            text_preprocessing_result = TextPreprocessingResult(payload.get("message", {}))
        else:
            event = self.get_action_name(payload, user)
            text_preprocessing_result = TextPreprocessingResult({})
        answer = await self.dialogue_manager.run_statemachine(event, text_preprocessing_result, user)
        if not answer:
            if payload.get("message"):
                answer = await HandlerText.run(self=self, payload=payload, user=user)
            else:
                answer = await HandlerServerAction.run(self=self, payload=payload, user=user)
        return answer


class SMHandlerText(HandlerText):
    """
    # Переопределение обработчика для MessageToSkill.
    """

    async def run(self, payload: Any, user: SMUser) -> List[Command]:
        """
        ## Запуск обработчика.

        Args:
            payload: Payload.
            user (SMUser): Объект NLPF User.

        Returns:
            List[Command]
        """
        text_preprocessing_result = TextPreprocessingResult(payload.get("message", {}))
        answer = await self.dialogue_manager.run_statemachine(
            text_preprocessing_result=text_preprocessing_result, user=user,
        )
        if not answer:
            answer = await super(SMHandlerText, self).run(payload=payload, user=user)
        else:
            monitoring.counter_incoming(
                self.app_name, user.message.message_name, self.__class__.__name__, user, app_info=user.message.app_info,
            )
        return answer


class SMDefaultMessageHandler(HandlerBase):
    """
    # Переопределение дефолтного обработчика запросов.
    """

    def __init__(self, app_name: str, dialogue_manager: SMDialogueManager = None) -> None:
        super(SMDefaultMessageHandler, self).__init__(app_name=app_name)
        self.dialogue_manager = dialogue_manager

    async def run(self, payload: Any, user: SMUser) -> List[Command]:
        """
        ## Запуск обработчика.

        Args:
            payload: Payload.
            user (SMUser): Объект NLPF User.

        Returns:
            List[Command]
        """
        event = user.message_pd.messageName
        answer = await self.dialogue_manager.run_statemachine(event, TextPreprocessingResult({}), user)
        if not answer:
            answer = await super(SMDefaultMessageHandler, self).run(payload=payload, user=user)
        else:
            monitoring.counter_incoming(
                self.app_name, user.message.message_name, self.__class__.__name__, user, app_info=user.message.app_info,
            )
        return answer


class SMHandlerTimeout(HandlerTimeout):
    """
    # Переопределение обработчика таймаута.
    """

    def __init__(self, app_name: str, dialogue_manager: SMDialogueManager = None) -> None:
        super(SMHandlerTimeout, self).__init__(app_name=app_name)
        self.dialogue_manager = dialogue_manager

    async def run(self, payload: Any, user: SMUser) -> List[Command]:
        """
        ## Запуск обработчика.

        Args:
            payload: Payload.
            user (SMUser): Объект NLPF User.

        Returns:
            List[Command]
        """
        event = Event.LOCAL_TIMEOUT
        answer = await self.dialogue_manager.run_statemachine(event, TextPreprocessingResult({}), user)
        if not answer:
            answer = await super(SMHandlerTimeout, self).run(payload=payload, user=user)
        return answer


class SMHandlerCloseApp(HandlerCloseApp):
    """
    # Переопределение обработчика таймаута.
    """

    def __init__(self, app_name: str, dialogue_manager: SMDialogueManager = None) -> None:
        super(SMHandlerCloseApp, self).__init__(app_name=app_name)
        self.dialogue_manager = dialogue_manager

    async def run(self, payload: Any, user: SMUser) -> List[Command]:
        """
        ## Запуск обработчика.

        Args:
            payload: Payload.
            user (SMUser): Объект NLPF User.

        Returns:
            List[Command]
        """
        event = RequestMessageName.CLOSE_APP
        answer = await self.dialogue_manager.run_statemachine(event, TextPreprocessingResult({}), user)
        if not answer:
            answer = await super(SMHandlerCloseApp, self).run(payload=payload, user=user)
        return answer


class SMSmartAppModel(SmartAppModel):
    """
    # Переопределение SmartAppModel.
    """

    def __init__(self, resources: SmartAppResources,
                 dialogue_manager_cls: Type[SMDialogueManager],
                 custom_settings: Any, **kwargs) -> None:
        super(SMSmartAppModel, self).__init__(resources, dialogue_manager_cls, custom_settings, **kwargs)
        self.scenario_descriptions["behaviors"].update_item(
            "nlpf_statemachine",
            {
                "success_action": "statemachine_success_action",
                "timeout": INTEGRATION_TIMEOUT,
            },
        )

        # параметр SERVER_ACTION = server_action !!! :(
        self._handlers[RequestMessageName.SERVER_ACTION] = SMHandlerServerAction(
            self.app_name, dialogue_manager=self.dialogue_manager,
        )
        self._handlers[RequestMessageName.CLOSE_APP] = SMHandlerCloseApp(
            self.app_name, dialogue_manager=self.dialogue_manager,
        )
        self._handlers[RequestMessageName.RUN_APP] = SMRunAppHandler(
            self.app_name, dialogue_manager=self.dialogue_manager,
        )
        self._handlers[RequestMessageName.MESSAGE_TO_SKILL] = SMHandlerText(
            self.app_name, dialogue_manager=self.dialogue_manager,
        )
        self._handlers[DEFAULT] = SMDefaultMessageHandler(self.app_name, dialogue_manager=self.dialogue_manager)
        self._handlers[Event.LOCAL_TIMEOUT] = SMHandlerTimeout(self.app_name, dialogue_manager=self.dialogue_manager)

    def get_handler(self, message_type: str) -> HandlerBase:
        """
        # Поиск нужного обработчика.

        Args:
            message_type (str): тип запроса;

        Returns:
            HandlerBase
        """
        if message_type in self._handlers:
            return self._handlers[message_type]
        return self._handlers[DEFAULT]


class SMHandlerRespond(HandlerRespond):
    """
    # Переопределение HandlerRespond.
    """

    def __init__(self, app_name: str, action_name: str = None, dialogue_manager: SMDialogueManager = None) -> None:
        super(SMHandlerRespond, self).__init__(app_name=app_name, action_name=action_name)
        self.dialogue_manager = dialogue_manager

    async def run(self, payload: Any, user: SMUser) -> List[Command]:
        """
        ## Запуск обработчика.

        Args:
            payload: Payload.
            user (SMUser): Объект NLPF User.

        Returns:
            List[Command]
        """
        event = user.message_pd.messageName
        answer = await self.dialogue_manager.run_statemachine(event, TextPreprocessingResult({}), user)
        if not answer:
            answer = await super(SMHandlerRespond, self).run(payload, user)
        else:
            monitoring.counter_incoming(
                self.app_name, event, self.__class__.__name__, user, app_info=user.message.app_info,
            )
        return answer

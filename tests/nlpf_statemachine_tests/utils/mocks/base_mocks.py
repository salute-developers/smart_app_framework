"""
# Коллекция базовых моков для NLPF StateMachine.
"""

from typing import Dict, Optional, Type, Union

from core.logging.logger_utils import behaviour_log
from core.message.from_message import SmartAppFromMessage
from core.text_preprocessing.preprocessing_result import TextPreprocessingResult
from nlpf_statemachine.models import BaseMessage, MessageToSkillPayload
from nlpf_statemachine.override import SMUser
from scenarios.user.parametrizer import Parametrizer
from tests.nlpf_statemachine_tests.utils.base import random_string
from .core import TestsCore
from .message_mocks import MessageMocks


class BaseMocks(MessageMocks):
    """
    # Базовые моки для NLPF StateMachine.
    """

    def __init__(self, core: TestsCore) -> None:
        self.core = core

    def smart_app_from_message(
            self,
            message: Optional[Dict] = None,
            headers: Optional[dict] = None,
    ) -> SmartAppFromMessage:
        """## Мок объекта SmartAppFromMessage."""
        if not message:
            message = self.message_to_skill().dict()

        return SmartAppFromMessage(
            value=message,
            headers=headers if headers else {},
            headers_required=bool(headers),
        )

    def user(
            self,
            message: Optional[Union[SmartAppFromMessage, BaseMessage, Dict]] = None,
            headers: Optional[Dict] = None,
            db_data: str = "{}",
            user_cls: Optional[Type[SMUser]] = SMUser,
    ) -> SMUser:
        """
        ## Мок объекта User.

        Args:
            message (SmartAppFromMessage, optional): пришедшее сообщение;
            headers (Dict, optional): Заголовки, пришедшие вместе с зарпосом;
            db_data (str, optional): Данные из БД в виде json;
            user_cls (Type[SMUser], optional): Класс для объекта User.

        Returns:
            SMUser: Объект User для стейт-машины.
        """
        if not headers:
            headers = {}
        if not message:
            message = self.smart_app_from_message(headers=headers)
        elif isinstance(message, Dict):
            message = self.smart_app_from_message(message=message, headers=headers)
        elif issubclass(type(message), BaseMessage):
            message = self.smart_app_from_message(message=message.dict(), headers=headers)
        else:
            behaviour_log(f"Wrong type of message in user mock: {type(message)}.", level="ERROR")

        self.core.descriptions["behaviors"].update_item(
            "nlpf_statemachine",
            {
                "success_action": "statemachine_success_action",
                "timeout": 2,
            },
        )
        return user_cls(
            id=random_string(),
            message=message,
            db_data=db_data,
            settings=self.core.settings,
            descriptions=self.core.descriptions,
            parametrizer_cls=Parametrizer,
            load_error=False,
        )

    @staticmethod
    def text_preprocessing_result(payload: Optional[Dict] = None) -> TextPreprocessingResult:
        """## Мок объекта TextPreprocessingResult."""
        if isinstance(payload, dict):
            return TextPreprocessingResult(payload.get("message", {}) if payload else {})
        elif isinstance(payload, MessageToSkillPayload):
            return TextPreprocessingResult(payload.message.dict())
        return TextPreprocessingResult({})

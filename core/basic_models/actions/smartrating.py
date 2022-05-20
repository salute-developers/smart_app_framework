from typing import Dict, Any, Optional, List, Union

from core.basic_models.actions.basic_actions import CommandAction
from core.basic_models.actions.command import Command
from core.configs.global_constants import KAFKA
from core.text_preprocessing.base import BaseTextPreprocessingResult
from scenarios.user.user_model import User
from smart_kit.configs import settings

CALL_RATING = "CALL_RATING"
ASK_RATING = "ASK_RATING"


class SmartRatingAction(CommandAction):
    DEFAULT_KAFKA_KEY = "main"

    def __init__(self, items: Dict[str, Any], id: Optional[str] = None):
        super().__init__(items, id)
        config = settings.Settings()
        settings_kafka_key = config["template_settings"].get("smartrating_kafka_key")
        self.kafka_key = items.get("kafka_key") or settings_kafka_key or self.DEFAULT_KAFKA_KEY
        self.request_data = {
            "topic_key": "toDP",
            "kafka_key": self.kafka_key,
            "kafka_replyTopic":
                config["kafka"]["template-engine"][self.kafka_key]["consumer"]["topics"]["smartrating"]
        }

    def run(self, user: User, text_preprocessing_result: BaseTextPreprocessingResult,
            params: Optional[Dict[str, Union[str, float, int]]] = None) -> Optional[List[Command]]:
        commands = [Command(self.command, {}, self.id, request_type=KAFKA, request_data=self.request_data)]
        return commands


class CallRatingAction(SmartRatingAction):
    """Action запроса оценки смартапа у пользователя по его инициативе через SmartRating API

    https://developers.sber.ru/docs/ru/va/reference/smartservices/smartrating/api
    Example::
        {
            "type": "call_rating",
            "kafka_key": "some_key" // опциональный параметр, по умолчанию "main"
        }
    """
    def __init__(self, items: Dict[str, Any], id: Optional[str] = None):
        items["command"] = CALL_RATING
        super().__init__(items, id)


class AskRatingAction(SmartRatingAction):
    """Action запроса оценки смартапа у пользователя без его инициативы через SmartRating API

    Документация для внутренних разработчиков: https://confluence.sberbank.ru/display/SMDG/API+SmartRating
    Example::
        {
            "type": "ask_rating",
            "kafka_key": "some_key" // опциональный параметр, по умолчанию "main"
        }
    """
    def __init__(self, items: Dict[str, Any], id: Optional[str] = None):
        items["command"] = ASK_RATING
        super().__init__(items, id)

from typing import Dict, Any, Optional, List, Union

from core.basic_models.actions.command import Command
from core.basic_models.actions.string_actions import StringAction
from core.text_preprocessing.base import BaseTextPreprocessingResult
from scenarios.user.user_model import User


CALL_RATING = "CALL_RATING"
ASK_RATING = "ASK_RATING"


class SmartRatingAction(StringAction):
    kafka_key = None
    DEFAULT_KAFKA_KEY = "main"

    def run(self, user: User, text_preprocessing_result: BaseTextPreprocessingResult,
            params: Optional[Dict[str, Union[str, float, int]]] = None) -> Optional[List[Command]]:
        settings_kafka_key = user.settings["template_settings"].get("smartrating_kafka_key")
        self.request_data = {
            "topic_key": "toDP",
            "kafka_key": self.kafka_key or settings_kafka_key or self.DEFAULT_KAFKA_KEY,
            "kafka_replyTopic": user.settings["template_settings"]["consumer_topic"]
        }

        return super().run(user, text_preprocessing_result, params)


class CallRatingAction(SmartRatingAction):
    def __init__(self, items: Dict[str, Any], id: Optional[str] = None):
        self.kafka_key = items.get("kafka_key")
        items["command"] = CALL_RATING
        super().__init__(items, id)


class AskRatingAction(SmartRatingAction):
    def __init__(self, items: Dict[str, Any], id: Optional[str] = None):
        self.kafka_key = items.get("kafka_key")
        items["command"] = ASK_RATING
        super().__init__(items, id)

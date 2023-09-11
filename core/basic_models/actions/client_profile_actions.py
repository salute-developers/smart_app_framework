from typing import Dict, Any, Optional, Union, AsyncGenerator

from core.basic_models.actions.command import Command
from core.basic_models.actions.string_actions import StringAction
from core.configs.config_constants import REPLY_TOPIC_KEY
from core.configs.global_constants import KAFKA, KAFKA_REPLY_TOPIC
from core.text_preprocessing.base import BaseTextPreprocessingResult
from core.utils.pickle_copy import pickle_deepcopy
from scenarios.user.user_model import User
from smart_kit.configs import settings

GIVE_ME_MEMORY = "GIVE_ME_MEMORY"
REMEMBER_THIS = "REMEMBER_THIS"


class GiveMeMemoryAction(StringAction):
    """
    Example::
        {
            "type": "give_me_memory",
            "behavior": "client_info_request",
            "nodes": {
                "memory": {
                    "confidentialMemo": [
                        "userAgreement"
                    ],
                    "projectPrivateMemo": [
                        "character_{{message.uuid.userId}}"
                    ]
                },
                "profileEmployee": {
                    "type": "unified_template",
                    "template": "{{ 0 }}",
                    "loader": "json"
                },
                "tokenType": {
                    "type": "unified_template",
                    "template": "{{ 0 }}",
                    "loader": "json"
                }
            }
        }
    """
    DEFAULT_KAFKA_KEY = "main"

    def __init__(self, items: Dict[str, Any], id: Optional[str] = None):
        super().__init__(items, id)
        config = settings.Settings()
        self.command = GIVE_ME_MEMORY
        self.request_type = KAFKA
        self.kafka_key: Optional[str] = items.get("kafka_key")
        self.behavior: Optional[str] = items.get("behavior")
        self._nodes.update({
            "root_nodes": {
                "protocolVersion": items.get("protocolVersion", 1)
            },
            "memory": [
                {"memoryPartition": key, "tags": val} for key, val in self._nodes["memory"].items()
            ],
            "consumer": {
                "projectId": config["template_settings"]["project_id"]
            }
        })
        settings_kafka_key = config["template_settings"].get("client_profile_kafka_key")
        self.kafka_key: str = self.kafka_key or settings_kafka_key or self.DEFAULT_KAFKA_KEY
        if self.request_data is None:
            self.request_data = dict()
        if "topic_key" not in self.request_data:
            self.request_data["topic_key"] = "client_info"
        if "kafka_key" not in self.request_data:
            self.request_data["kafka_key"] = self.kafka_key
        if REPLY_TOPIC_KEY not in self.request_data and KAFKA_REPLY_TOPIC not in self.request_data:
            self.request_data[KAFKA_REPLY_TOPIC] = config["template_settings"]["consumer_topic"]

    async def run(self, user: User, text_preprocessing_result: BaseTextPreprocessingResult,
                  params: Optional[Dict[str, Union[str, float, int]]] = None) -> AsyncGenerator[Command, None]:
        if self.behavior:
            callback_id = user.message.generate_new_callback_id()
            scenario_id = user.last_scenarios.last_scenario_name if hasattr(user, 'last_scenarios') else None
            user.behaviors.add(callback_id, self.behavior, scenario_id,
                               text_preprocessing_result.raw, pickle_deepcopy(params))

        async for command in super().run(user, text_preprocessing_result, params):
            yield command


class RememberThisAction(StringAction):
    """
    Example::
      {
        "type": "remember_this",
        "nodes": {
          "clientIds": {
            "type": "unified_template",
            "template": "{{ 0 }}",
            "loader": "json"
          },
          "memory": [
            {
              "memoryPartition": "publicMemo",
              "partitionData": [
                {
                  "tag": "historyInfo",
                  "action": {
                    "type": "upsert",
                    "params": {
                      "operation": [
                        {
                          "selector": {
                            "intent": {
                              "$eq": "run_app"
                            },
                            "surface": {
                              "$eq": "{{ 0 }}"
                            },
                            "channel": {
                              "$eq": "{{ 0 }}"
                            },
                            "projectId": {
                              "$eq": "{{ 0 }}"
                            }
                          },
                          "updater": [
                            {
                              "$set": {
                                "$.lastExecuteDateTime": "{{ 0 }}"
                              }
                            },
                            {
                              "$inc": {
                                "$.executeCounter": 1
                              }
                            }
                          ]
                        }
                      ]
                    }
                  }
                }
              ]
            }
          ]
        }
      }
    """
    DEFAULT_KAFKA_KEY = "main"

    def __init__(self, items: Dict[str, Any], id: Optional[str] = None):
        super().__init__(items, id)
        self.command = REMEMBER_THIS
        self.request_type = KAFKA
        self.kafka_key: Optional[str] = items.get("kafka_key")
        self._nodes.update({
            "root_nodes": {
                "protocolVersion": items.get("protocolVersion", 3)
            }
        })

    async def run(self, user: User, text_preprocessing_result: BaseTextPreprocessingResult,
                  params: Optional[Dict[str, Union[str, float, int]]] = None) -> AsyncGenerator[Command, None]:
        self._nodes.update({
            "consumer": {
                "projectId": user.settings["template_settings"]["project_id"]
            }
        })
        if self.request_data is None:
            self.request_data = dict()
        if "topic_key" not in self.request_data:
            self.request_data["topic_key"] = "client_info_remember"
        if "kafka_key" not in self.request_data:
            settings_kafka_key: Optional[str] = user.settings["template_settings"].get("client_profile_kafka_key")
            kafka_key: str = self.kafka_key or settings_kafka_key or self.DEFAULT_KAFKA_KEY
            self.request_data["kafka_key"] = kafka_key
        if REPLY_TOPIC_KEY not in self.request_data and KAFKA_REPLY_TOPIC not in self.request_data:
            self.request_data[KAFKA_REPLY_TOPIC] = user.settings["template_settings"]["consumer_topic"]

        async for command in super().run(user, text_preprocessing_result, params):
            yield command

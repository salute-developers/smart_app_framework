import time
from copy import copy
from typing import Dict, Any, Optional, Union, List

from core.basic_models.actions.command import Command
from core.basic_models.actions.string_actions import StringAction
from core.text_preprocessing.base import BaseTextPreprocessingResult
from scenarios.user.user_model import User
from scenarios.actions.action_params_names import (SAVED_MESSAGES, REQUEST_FIELD, TO_MESSAGE_PARAMS, TO_MESSAGE_NAME)
from core.configs.global_constants import KAFKA, CALLBACK_ID_HEADER
from smart_kit.configs import settings
from smart_kit.names.action_params_names import SEND_TIMESTAMP

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
        self.kafka_key = items.get("kafka_key")
        self.behavior = items.get("behavior")
        self._nodes.update({
            "root_nodes": {
                "protocolVersion": items.get("protocolVersion") or 1
            },
            "memory": [
                {"memoryPartition": key, "tags": val} for key, val in self._nodes["memory"].items()
            ],
            "consumer": {
                "projectId": config["template_settings"]["project_id"]
            }
        })
        settings_kafka_key = config["template_settings"].get("client_profile_kafka_key")
        self.request_data = self.request_data = {
            "topic_key": "client_info",
            "kafka_key": self.kafka_key or settings_kafka_key or self.DEFAULT_KAFKA_KEY,
            "kafka_replyTopic": config["kafka"]["template-engine"]["main"]["consumer"]["topics"]["client_profile"]
        }

    def run(self, user: User, text_preprocessing_result: BaseTextPreprocessingResult,
            params: Optional[Dict[str, Union[str, float, int]]] = None) -> Optional[List[Command]]:
        if self.behavior:
            action_params = copy(params or {})
            command_params = dict()
            collected = user.parametrizer.collect(text_preprocessing_result, filter_params={"command": self.command})
            action_params.update(collected)

            for key, value in self.nodes.items():
                rendered = self._get_rendered_tree(value, action_params, self.no_empty_nodes)
                if rendered != "" or not self.no_empty_nodes:
                    command_params[key] = rendered

            callback_id = user.message.generate_new_callback_id()
            request_data = copy(self.request_data or {})
            request_data.update(self._get_extra_request_data(user, params, callback_id))

            scenario = user.last_scenarios.last_scenario_name if hasattr(user, 'last_scenarios') else None

            save_params = self._get_save_params(user, action_params, command_params)
            user.behaviors.add(
                callback_id,
                self.behavior,
                scenario,
                text_preprocessing_result.raw,
                save_params,
            )

        commands = super().run(user, text_preprocessing_result, params)
        return commands

    def _get_save_params(self, user, action_params, command_action_params):
        save_params = self._get_rendered_tree_recursive({}, action_params)
        save_params.update({SAVED_MESSAGES: action_params.get(SAVED_MESSAGES, {})})
        save_params.update({REQUEST_FIELD: action_params.get(REQUEST_FIELD, {})})
        save_params.update({SEND_TIMESTAMP: time.time()})

        if user.settings["template_settings"].get("self_service_with_state_save_messages", True):
            saved_messages = save_params[SAVED_MESSAGES]
            if user.message.message_name not in saved_messages or self.rewrite_saved_messages:
                saved_messages[user.message.type] = user.message.payload

        save_params.update({TO_MESSAGE_PARAMS: command_action_params})
        save_params.update({TO_MESSAGE_NAME: self.command})
        return save_params

    def _get_extra_request_data(self, user, params, callback_id):
        extra_request_data = {CALLBACK_ID_HEADER: callback_id}
        return extra_request_data


class RememberThisAction(StringAction):
    """
    Example::
      {
        "type": "remember",
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
        config = settings.Settings()
        self.command = REMEMBER_THIS
        self.request_type = KAFKA
        self.kafka_key = items.get("kafka_key")
        self._nodes.update({
            "root_nodes": {
                "protocolVersion": items.get("protocolVersion") or 3
            },
            "consumer": {
                "projectId": config["template_settings"]["project_id"]
            }
        })
        settings_kafka_key = config["template_settings"].get("client_profile_kafka_key")
        self.request_data = {
            "topic_key": "client_info_remember",
            "kafka_key": self.kafka_key or settings_kafka_key or self.DEFAULT_KAFKA_KEY,
            "kafka_replyTopic": config["kafka"]["template-engine"]["main"]["consumer"]["topics"]["client_profile"]
        }

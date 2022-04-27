import time
from copy import copy
from typing import Dict, Any, Optional, Union, List

from core.basic_models.actions.command import Command
from core.basic_models.actions.string_actions import StringAction
from core.logging.logger_utils import log
from core.model.base_user import BaseUser
from core.text_preprocessing.base import BaseTextPreprocessingResult
from core.utils.pickle_copy import pickle_deepcopy
from scenarios.user.user_model import User
from core.configs.global_constants import KAFKA

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
        self.command = GIVE_ME_MEMORY
        self.request_type = KAFKA
        self.kafka_key = items.get("kafka_key")
        self.behavior = items.get("behavior")
        self._nodes["root_nodes"] = {"protocolVersion": items.get("protocolVersion") or 1}
        self._nodes["memory"] = [
            {"memoryPartition": key, "tags": val} for key, val in self._nodes["memory"].items()
        ]
        self.callback_id_header = items.get("callback_id_header")

    def run(self, user: User, text_preprocessing_result: BaseTextPreprocessingResult,
            params: Optional[Dict[str, Union[str, float, int]]] = None) -> Optional[List[Command]]:
        self._nodes["consumer"] = {"projectId": user.settings["template_settings"]["project_id"]}

        settings_kafka_key = user.settings["template_settings"].get("client_profile_kafka_key")
        self.request_data = {
            "topic_key": "client_info",
            "kafka_key": self.kafka_key or settings_kafka_key or self.DEFAULT_KAFKA_KEY,
            "kafka_replyTopic": user.settings["template_settings"]["consumer_topic"]
        }

        if self.behavior:
            action_params = params or {}
            command_params = self._get_command_params(user, action_params)
            save_action_params = self._render_behavior_params(action_params, command_params)
            scenario_id = user.last_scenarios if hasattr(user, 'last_scenarios') else None
            user.behaviors.add(user.message.generate_new_callback_id(), self.behavior, scenario_id,
                               text_preprocessing_result.raw, action_params=pickle_deepcopy(params))

        commands = super().run(user, text_preprocessing_result, params)
        return commands

    def _render_behavior_params(self, action_params, command_params):
        behavior_params = self._render_data({}.items(), action_params)
        behavior_params.update({"pass_through": action_params.get("pass_through", {})})
        behavior_params.update({"debug_info": action_params.get("debug_info", {})})
        behavior_params.update({"to_message_params": command_params})
        behavior_params.update({"send_timestamp": time.time()})
        to_message_name = self.command
        behavior_params.update({"to_message_name": to_message_name})

    def _render_data(self, render_items, action_params):
        render_data = {}
        for key, value in render_items:
            rendered = self._get_rendered_tree(value, action_params, self.no_empty_nodes)
            if rendered != "" or not self.no_empty_nodes:
                render_data[key] = rendered
        return render_data

    def _get_command_params(self, user: BaseUser, action_params):
        command_params = {}
        if user.settings["template_settings"].get("debug_info"):
            saved_debug_info = action_params.get("debug_info", {})
            message_debug_info = user.message.debug_info
            if message_debug_info.get("debug_info_key"):
                app_debug_info = saved_debug_info.setdefault(message_debug_info["debug_info_key"], [])
                app_debug_info.append(message_debug_info)
            command_params["debug_info"] = saved_debug_info
        return command_params

    def _save_behavior(self, user, request_data, text_preprocessing_result, action_params):
        callback_id = user.message.generate_new_callback_id()
        if self.callback_id_header:
            request_data[self.callback_id_header] = callback_id
        to_message_params_to_save = copy(action_params.get("to_message_params", {}))
        saved_to_message_params_fields = {
            "intent", "intent_meta",
            "original_intent", "app_info", "projectName", "new_session",
            "applicationId", "appversionId", "domain_search", "status_code",
            "permitted_actions", "caller_app_info"
        }
        for key in tuple(to_message_params_to_save.keys()):
            if key not in saved_to_message_params_fields:
                to_message_params_to_save.pop(key, None)
        action_params_to_save = copy(action_params)
        action_params_to_save["to_message_params"] = to_message_params_to_save
        log(f'GiveMeMemoryAction._save_behavior action_params_to_save: %(action_params_to_save)s', user=user, params={
            'action_params_to_save': str(action_params_to_save)
        }, level='DEBUG')
        user.behaviors.add(callback_id, self.behavior, None, text_preprocessing_result.raw, action_params_to_save)


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
        self.command = REMEMBER_THIS
        self.request_type = KAFKA
        self.kafka_key = items.get("kafka_key")
        self._nodes["root_nodes"] = {"protocolVersion": items.get("protocolVersion") or 3}

    def run(self, user: User, text_preprocessing_result: BaseTextPreprocessingResult,
            params: Optional[Dict[str, Union[str, float, int]]] = None) -> Optional[List[Command]]:
        self._nodes["consumer"] = {"projectId": user.settings["template_settings"]["project_id"]}

        settings_kafka_key = user.settings["template_settings"].get("client_profile_kafka_key")
        self.request_data = {
            "topic_key": "client_info_remember",
            "kafka_key": self.kafka_key or settings_kafka_key or self.DEFAULT_KAFKA_KEY,
            "kafka_replyTopic": user.settings["template_settings"]["consumer_topic"]
        }

        commands = super().run(user, text_preprocessing_result, params)
        return commands

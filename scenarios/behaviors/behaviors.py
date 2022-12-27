# coding: utf-8
import math
import socket
from collections import namedtuple
from time import time
from typing import Dict, List

import scenarios.logging.logger_constants as log_const
from core.basic_models.actions.command import Command
from core.logging.logger_utils import log
from core.names.field import APP_INFO
from core.text_preprocessing.preprocessing_result import TextPreprocessingResult
from core.utils.pickle_copy import pickle_deepcopy
from scenarios.actions.action_params_names import TO_MESSAGE_NAME, TO_MESSAGE_PARAMS, LOCAL_VARS
from core.monitoring.monitoring import monitoring


Callback = namedtuple(
    "Callback", "behavior_id expire_time scenario_id text_preprocessing_result action_params hostname"
)


class Behaviors:
    EXPIRATION_DELAY = 1

    def __init__(self, items, descriptions, user):
        self._items = items or {}
        self.descriptions = descriptions
        self._user = user
        self.Callback = Callback
        self._callbacks: Dict[str, Callback] = {}
        self._behavior_timeouts = []
        self._returned_callbacks = []

    def initialize(self):
        """Should be invoked after __init__"""
        for key, callback in self._items.items():
            callback.setdefault("text_preprocessing_result", {})
            callback.setdefault("action_params", {})
            callback.setdefault("hostname", None)
            self._callbacks[key] = self.Callback(**callback)

        callback_id = self._user.message.callback_id
        callback = self._get_callback(callback_id)
        if callback:
            callback_action_params = callback.action_params
            for key, value in callback_action_params.get(LOCAL_VARS, {}).items():
                self._user.local_vars.set(key, value)

    def _add_behavior_timeout(self, time_left, callback_id):
        self._behavior_timeouts.append((time_left, callback_id))

    def get_behavior_timeouts(self):
        return self._behavior_timeouts

    def _add_returned_callback(self, callback_id):
        self._returned_callbacks.append(callback_id)

    def get_returned_callbacks(self):
        return self._returned_callbacks

    def add(
        self, callback_id: str, behavior_id, scenario_id=None, text_preprocessing_result_raw=None, action_params=None
    ):
        host = socket.gethostname()
        text_preprocessing_result_raw = text_preprocessing_result_raw or {}
        # behavior will be removed after now + timeout + EXPIRATION_DELAY
        expiration_time = math.ceil(time()) + self.descriptions[behavior_id].timeout(self._user) + self.EXPIRATION_DELAY
        action_params = action_params or dict()
        action_params[LOCAL_VARS] = pickle_deepcopy(self._user.local_vars.values)

        callback = self.Callback(
            behavior_id=behavior_id,
            expire_time=expiration_time,
            scenario_id=scenario_id,
            text_preprocessing_result=text_preprocessing_result_raw,
            action_params=action_params,
            hostname=host,
        )
        self._callbacks[callback_id] = callback
        log(f"behavior.add: adding behavior %({log_const.BEHAVIOR_ID_VALUE})s with scenario_id"
            f" %({log_const.CHOSEN_SCENARIO_VALUE})s for callback %({log_const.BEHAVIOR_CALLBACK_ID_VALUE})s"
            f" expiration_time: %(expiration_time)s.",
            user=self._user,
            params={
                log_const.KEY_NAME: log_const.BEHAVIOR_ADD_VALUE,
                log_const.BEHAVIOR_CALLBACK_ID_VALUE: callback_id,
                log_const.BEHAVIOR_ID_VALUE: behavior_id,
                log_const.CHOSEN_SCENARIO_VALUE: scenario_id,
                "expiration_time": int(expiration_time),
            },
            )

        behavior_description = self.descriptions[behavior_id]
        # add timer with now + behavior.timeout eval time
        expire_time_us = behavior_description.get_expire_time_from_now(self._user)
        self._add_behavior_timeout(expire_time_us, callback_id)

    def _delete(self, callback_id):
        if callback_id in self._callbacks:
            del self._callbacks[callback_id]

    def clear_all(self):
        self._callbacks = {}

    def _log_callback(
        self, callback_id: str, log_name: str, metric, behavior_result: str, callback_action_params: Dict
    ):
        callback = self._get_callback(callback_id)
        behavior = self.descriptions[callback.behavior_id] if callback else None
        callback_action_params = callback_action_params or {}
        to_message_name = callback_action_params.get(TO_MESSAGE_NAME, "UNKNOWN_MESSAGE_NAME")
        metric(self._user.settings.app_name, to_message_name)
        log_params = {
            log_const.KEY_NAME: log_name,
            log_const.BEHAVIOR_CALLBACK_ID_VALUE: callback_id,
            log_const.BEHAVIOR_ID_VALUE: str(behavior.id),
            log_const.CHOSEN_SCENARIO_VALUE: callback.scenario_id,
            "to_message_name": to_message_name,
            "behavior_result": behavior_result,
        }

        log(
            f"{self.__class__.__name__}.{behavior_result}:"
            f" found valid behavior %({log_const.BEHAVIOR_ID_VALUE})s with"
            f" scenario_id %({log_const.CHOSEN_SCENARIO_VALUE})s for"
            f" callback %({log_const.BEHAVIOR_CALLBACK_ID_VALUE})s with to_message_name %(to_message_name)s",
            user=self._user,
            params=log_params,
        )

    async def success(self, callback_id: str) -> List[Command]:
        callback = self._get_callback(callback_id)
        result = []
        if callback:
            self._check_hostname(callback_id, callback)
            self._add_returned_callback(callback_id)
            behavior = self.descriptions[callback.behavior_id]
            callback_action_params = callback.action_params
            self._log_callback(
                callback_id,
                "behavior_success",
                monitoring.counter_behavior_success,
                "success",
                callback_action_params,
            )
            text_preprocessing_result = TextPreprocessingResult(callback.text_preprocessing_result)
            result = await behavior.success_action.run(self._user, text_preprocessing_result, callback_action_params)
            result = result or []
        else:
            log(f"behavior.success not found valid callback for callback_id %({log_const.BEHAVIOR_CALLBACK_ID_VALUE})s",
                self._user,
                params={log_const.KEY_NAME: log_const.BEHAVIOR_SUCCESS_VALUE,
                        log_const.BEHAVIOR_CALLBACK_ID_VALUE: callback_id})
        self._delete(callback_id)
        return result

    async def fail(self, callback_id: str) -> List[Command]:
        callback = self._get_callback(callback_id)
        result = []
        if callback:
            self._check_hostname(callback_id, callback)
            self._add_returned_callback(callback_id)
            behavior = self.descriptions[callback.behavior_id]
            callback_action_params = callback.action_params
            self._log_callback(
                callback_id, "behavior_fail", monitoring.counter_behavior_fail, "fail", callback_action_params
            )
            text_preprocessing_result = TextPreprocessingResult(callback.text_preprocessing_result)
            result = await behavior.fail_action.run(self._user, text_preprocessing_result, callback_action_params) or []
        else:
            log(f"behavior.fail not found valid callback for callback_id %({log_const.BEHAVIOR_CALLBACK_ID_VALUE})s",
                self._user,
                params={log_const.KEY_NAME: log_const.BEHAVIOR_FAIL_VALUE,
                        log_const.BEHAVIOR_CALLBACK_ID_VALUE: callback_id})
        self._delete(callback_id)
        return result

    async def timeout(self, callback_id: str) -> List[Command]:
        callback = self._get_callback(callback_id)
        result = []
        if callback:
            self._add_returned_callback(callback_id)
            behavior = self.descriptions[callback.behavior_id]
            callback_action_params = callback.action_params
            self._log_callback(
                callback_id, "behavior_timeout", monitoring.counter_behavior_timeout, "timeout", callback_action_params
            )
            text_preprocessing_result = TextPreprocessingResult(callback.text_preprocessing_result)
            result = await behavior.timeout_action.run(self._user, text_preprocessing_result, callback_action_params)
            result = result or []
        else:
            log(f"behavior.timeout not found valid callback for callback_id %({log_const.BEHAVIOR_CALLBACK_ID_VALUE})s",
                self._user,
                params={log_const.KEY_NAME: log_const.BEHAVIOR_TIMEOUT_VALUE,
                        log_const.BEHAVIOR_CALLBACK_ID_VALUE: callback_id})
        self._delete(callback_id)
        return result

    async def misstate(self, callback_id: str) -> List[Command]:
        callback = self._get_callback(callback_id)
        result = []
        if callback:
            self._check_hostname(callback_id, callback)
            self._add_returned_callback(callback_id)
            behavior = self.descriptions[callback.behavior_id]
            callback_action_params = callback.action_params
            self._log_callback(
                callback_id,
                "behavior_misstate",
                monitoring.counter_behavior_misstate,
                "misstate",
                callback_action_params,
            )
            text_preprocessing_result = TextPreprocessingResult(callback.text_preprocessing_result)
            result = await behavior.misstate_action.run(self._user, text_preprocessing_result, callback_action_params)
            result = result or []
        else:
            log("behavior.misstate not found valid callback"
                f" for callback_id %({log_const.BEHAVIOR_CALLBACK_ID_VALUE})s",
                self._user,
                params={log_const.KEY_NAME: log_const.BEHAVIOR_MISSTATE_VALUE,
                        log_const.BEHAVIOR_CALLBACK_ID_VALUE: callback_id})
        self._delete(callback_id)
        return result

    def _get_callback(self, callback_id):
        callback = self._callbacks.get(callback_id)
        return callback

    def has_callback(self, callback_id):
        callback = self._get_callback(callback_id)
        return callback is not None

    def get_callback_action_params(self, callback_id):
        callback = self._get_callback(callback_id)
        if callback:
            return callback.action_params

    def check_misstate(self, callback_id: str):
        log(
            f"behavior.check_misstate started: got callback %({log_const.BEHAVIOR_CALLBACK_ID_VALUE})s.",
            self._user,
            params={
                log_const.KEY_NAME: log_const.BEHAVIOR_CHECK_MISSTATE_VALUE,
                log_const.BEHAVIOR_CALLBACK_ID_VALUE: callback_id,
            },
        )
        callback = self._get_callback(callback_id)
        if callback:
            callback_scenario_id = callback.scenario_id
            if callback_scenario_id is not None:
                last_scenario_equal_callback_scenario = (
                    self._user.last_scenarios.last_scenario_name != callback_scenario_id
                )
                if not last_scenario_equal_callback_scenario:
                    log(
                        f"behavior.check_misstate:"
                        f" GOT MISSTATE for callback %({log_const.BEHAVIOR_CALLBACK_ID_VALUE})s:"
                        f" user_scenario: %(user_scenario)s, callback_scenario: %(callback_scenario)s.",
                        self._user,
                        params={
                            log_const.KEY_NAME: log_const.BEHAVIOR_CHECK_MISSTATE_VALUE,
                            log_const.BEHAVIOR_CALLBACK_ID_VALUE: callback_id,
                            "user_scenario": self._user.last_scenarios.last_scenario_name,
                            "callback_scenario": callback_scenario_id,
                        },
                        level="WARNING",
                    )
                return last_scenario_equal_callback_scenario

    def expire(self):
        callback_id_for_delete = []
        for callback_id, (behavior_id, expiration_time, *_) in self._callbacks.items():
            if expiration_time <= time():
                callback_id_for_delete.append(callback_id)
        for callback_id in callback_id_for_delete:
            callback_action_params = self.get_callback_action_params(callback_id)
            to_message_name = callback_action_params.get(TO_MESSAGE_NAME)
            monitoring.counter_behavior_expire(self._user.settings.app_name, to_message_name)
            log_params = {
                log_const.KEY_NAME: "behavior_expire",
                log_const.BEHAVIOR_CALLBACK_ID_VALUE: callback_id,
                log_const.BEHAVIOR_DATA_VALUE: str(self._callbacks[callback_id]),
                "to_message_name": to_message_name,
            }

            log(
                "behavior.expire:"
                f" if you see this - something went wrong(should be timeout in normal case)"
                f" callback %({log_const.BEHAVIOR_CALLBACK_ID_VALUE})s,  with to_message_name %(to_message_name)s",
                params=log_params,
                level="WARNING",
                user=self._user,
            )
            self._delete(callback_id)

    def check_got_saved_id(self, behavior_id):
        if self.descriptions[behavior_id].loop_def:
            for callback_id, (_behavior_id, *_) in self._callbacks.items():
                if _behavior_id == behavior_id:
                    log(
                        "behavior.check_got_saved_id == True:"
                        f" already got saved behavior %({log_const.BEHAVIOR_ID_VALUE})s"
                        f" for callback_id %({log_const.BEHAVIOR_CALLBACK_ID_VALUE})s",
                        user=self._user,
                        params={
                            log_const.KEY_NAME: "behavior_got_saved",
                            log_const.BEHAVIOR_CALLBACK_ID_VALUE: callback_id,
                            log_const.BEHAVIOR_ID_VALUE: behavior_id,
                            log_const.BEHAVIOR_DATA_VALUE: str(self._callbacks[callback_id]),
                        },
                    )
                    return True
            return False
        else:
            return False

    @property
    def raw(self):
        return {key: callback._asdict() for key, callback in self._callbacks.items()}

    def _get_to_message_name(self, callback_id):
        callback_action_params = self.get_callback_action_params(callback_id) or {}
        to_message_name = callback_action_params.get(TO_MESSAGE_NAME)
        return to_message_name

    def _check_hostname(self, callback_id, callback) -> None:
        host: str = socket.gethostname()
        if callback.hostname != host:
            log(
                f"behavior.check_hostname: current %({log_const.HOSTNAME})s and "
                f"last %({log_const.LAST_HOSTNAME})s hostname are not equal on the same message_id.",
                user=self._user,
                params={
                    log_const.KEY_NAME: log_const.CHECK_HOSTNAME,
                    log_const.BEHAVIOR_CALLBACK_ID_VALUE: callback_id,
                    log_const.BEHAVIOR_ID_VALUE: callback.behavior_id,
                    log_const.CHOSEN_SCENARIO_VALUE: callback.scenario_id,
                    log_const.MESSAGE_ID: self._user.message.logging_uuid,
                    log_const.HOSTNAME: host,
                    log_const.LAST_HOSTNAME: callback.hostname,
                },
            )
            monitoring.counter_host_has_changed(self._user.settings.app_name)

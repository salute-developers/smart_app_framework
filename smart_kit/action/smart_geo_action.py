from typing import Dict, Any, Optional, Union, AsyncGenerator

from core.basic_models.actions.command import Command
from core.basic_models.actions.string_actions import StringAction
from core.text_preprocessing.base import BaseTextPreprocessingResult
from core.utils.pickle_copy import pickle_deepcopy
from scenarios.user.user_model import User
from smart_kit.names.message_names import GET_PROFILE_DATA


class SmartGeoAction(StringAction):
    """Action для получения геоданных пользователя

    Описание smart geo сервиса: https://developers.sber.ru/docs/ru/va/reference/smartservices/smartgeo/overview
    Условия подключение smart geo: https://developers.sber.ru/docs/ru/va/reference/smartservices/smartgeo/conditions
    Описание smart geo API: https://developers.sber.ru/docs/ru/va/reference/smartservices/smartgeo/api

    ## Использование:
    Внимание: action поддерживает только смартаппы, использующие `MAIN_LOOP = MainLoop` (задаётся в _app_config.py_),
    где `from smart_kit.start_points.main_loop_kafka import MainLoop`.
    ```
    {
      "type": "smart_geo",
      "behavior": "smart_geo_behavior"
    }
    ```
    Опциональный параметр `"behavior"` определяет Behavior, используемый в запросе.

    После исполнения команды и успешного ответа от smart geo API геоданные пользователя сохранятся в переменную внутри
    User `user.variables.smart_geo`
    """
    def __init__(self, items: Dict[str, Any], id: Optional[str] = None):
        super().__init__(items, id)
        self.command = GET_PROFILE_DATA
        self.behavior = items.get("behavior", "smart_geo_behavior")

    async def run(self, user: User, text_preprocessing_result: BaseTextPreprocessingResult,
                  params: Optional[Dict[str, Union[str, float, int]]] = None) -> AsyncGenerator[Command, None]:
        scenario_id = user.last_scenarios.last_scenario_name
        user.behaviors.add(user.message.generate_new_callback_id(), self.behavior, scenario_id,
                           text_preprocessing_result.raw, action_params=pickle_deepcopy(params))

        async for command in super().run(user, text_preprocessing_result, params):
            yield command

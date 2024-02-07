"""
# Переопределение NLPF DialogueManager.
"""
from typing import Dict, List, Optional, Tuple, Union

from pydantic import BaseModel

from core.basic_models.actions.command import Command
from core.descriptions.descriptions import Descriptions
from core.text_preprocessing.preprocessing_result import TextPreprocessingResult
from nlpf_statemachine.const import CONTEXT_MANAGER_ID, STATE_MACHINE_REPOSITORY_NAME
from nlpf_statemachine.models import Response
from nlpf_statemachine.override.user import SMUser
from smart_kit.models.dialogue_manager import DialogueManager


class SMDialogueManager(DialogueManager):
    """
    # DialogueManager для StateMachine.
    """

    def __init__(self, scenario_descriptions: Descriptions, app_name: str, **kwargs) -> None:
        super(SMDialogueManager, self).__init__(scenario_descriptions, app_name, **kwargs)
        self.state_machine_context_manager = scenario_descriptions[STATE_MACHINE_REPOSITORY_NAME]

    @staticmethod
    def _to_dict(model: Union[BaseModel, Dict]) -> Dict:
        """
        # Перевод параметров в dict.

        Args:
            model (Union[BaseModel, Dict]): Параметры в виде dict или pydantic модели.

        Returns:
            Dict: Параметры в виде словаря
        """
        if isinstance(model, dict):
            return model
        elif isinstance(model, BaseModel):
            return model.model_dump(exclude_none=True, by_alias=True)
        return {}

    def _process_response(self, response: Response) -> Tuple[Dict, Optional[str], Optional[dict]]:
        """
        # Формирование параметров ответа pydantic объекта Response.

        Args:
            response (Response): ответ от ContextManager.

        Returns:
            Tuple[Dict, Optional[str], Optional[dict]]
        """
        request_type = response.request_type if response.request_type else None
        request_data = self._to_dict(response.request_data)
        params = self._to_dict(response.payload)
        return params, request_type, request_data

    async def run_scenario(
            self, scen_id: str, text_preprocessing_result: TextPreprocessingResult, user: SMUser,
    ) -> List[Command]:
        """
        # Запуск сценария.

        Для кейса StateMachine попадём сюда сразу, так как для верхнего интента не найдём результата.

        Args:
            scen_id (str): наименование сценария;
            text_preprocessing_result (TextPreprocessingResult): NLPF TextPreprocessingResult;
            user (SMUser): NLPF User;

        Returns:
            List[Command]
        """
        answer = await self.run_statemachine(
            event=None, text_preprocessing_result=text_preprocessing_result, user=user,
        )
        if not answer:
            answer = await super(SMDialogueManager, self).run_scenario(
                scen_id=scen_id, text_preprocessing_result=text_preprocessing_result, user=user,
            )
        return answer

    async def run_statemachine(
            self, event: str = None, text_preprocessing_result: TextPreprocessingResult = None, user: SMUser = None,
    ) -> Optional[List[Command]]:
        """
        # Запуск стейт-машины (контекст-менеджера).

        Args:
            event (str): событие;
            text_preprocessing_result (TextPreprocessingResult): NLPF TextPreprocessingResult;
            user (SMUser): NLPF User;

        Returns:
            Optional[List[Command]]
        """
        context_manager = self.state_machine_context_manager.get(CONTEXT_MANAGER_ID)
        response = await context_manager.run(
            event=event, message=user.message_pd, context=user.context_pd,
            text_preprocessing_result=text_preprocessing_result, user=user,
        )
        if response:
            params, request_type, request_data = self._process_response(response)
            return [
                Command(
                    name=response.messageName, params=params, request_type=request_type, request_data=request_data,
                ),
            ]

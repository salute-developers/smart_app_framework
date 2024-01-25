"""
# Тесты на nlpf_statemachine.override.dialog_manager.
"""
from typing import List, Optional
from unittest.mock import MagicMock, patch

from pydantic import BaseModel

from core.basic_models.actions.command import Command
from nlpf_statemachine.models import AssistantResponsePayload, Response
from tests.nlpf_statemachine_tests.utils import SMTestCaseBase, random_guid


class TestScenarioSimpleEvent(SMTestCaseBase):
    """
    # Тесты на переопределение DialogManager.
    """

    SMART_KIT_APP_CONFIG = "nlpf_statemachine.example.app_config"

    @staticmethod
    def _assert_one_command(response: List[Command]) -> None:
        assert isinstance(response, list)
        assert len(response) == 1
        assert isinstance(response[0], Command)

    async def _run_statemachine(
            self,
            mock_response: Optional[Response],
            context_manager_run: MagicMock,
            success_run: bool = True,
    ) -> List[Command]:
        event: str = random_guid()
        context_manager_run.return_value = mock_response
        user = self.mocks.user()
        text_preprocessing_result = self.mocks.text_preprocessing_result()

        # ==== Run ====
        response = await self.core.dialogue_manager.run_statemachine(
            event=event,
            text_preprocessing_result=text_preprocessing_result,
            user=user,
        )

        # ==== Asserts ====
        context_manager_run.assert_called_with(
            event=event,
            message=user.message_pd,
            context=user.context_pd,
            text_preprocessing_result=text_preprocessing_result,
            user=user,
        )

        if success_run:
            self._assert_one_command(response=response)

        return response

    @patch("nlpf_statemachine.kit.context_manager.ContextManager.run")
    async def test_run_statemachine_blank(self, context_manager_run: MagicMock) -> None:
        """
        ## Тест на запуск стейт-машины без ответа.
        """
        response = await self._run_statemachine(
            mock_response=None,
            context_manager_run=context_manager_run,
            success_run=False,
        )
        assert response is None

    @patch("nlpf_statemachine.kit.context_manager.ContextManager.run")
    async def test_run_statemachine_1(self, context_manager_run: MagicMock) -> None:
        """
        # Тест на запуск стейт-машины с условиями 1.

        Условия:
            * payload: dict;
            * request_type: какая-то строка;
            * request_data: не пустой dict;
        """
        mock_response = Response(messageName="TestResponse")
        mock_response.payload = {"key": "value"}
        mock_response.request_type = random_guid()
        mock_response.request_data = {"key2": "value2"}

        response = await self._run_statemachine(mock_response=mock_response, context_manager_run=context_manager_run)

        assert response[0].name == mock_response.messageName
        assert response[0].request_type == mock_response.request_type
        assert response[0].request_data == mock_response.request_data
        assert response[0].payload == mock_response.payload

    @patch("nlpf_statemachine.kit.context_manager.ContextManager.run")
    async def test_run_statemachine_2(self, context_manager_run: MagicMock) -> None:
        """
        ## Тест на запуск стейт-машины с условиями 2.

        Условия:
            * payload: pydantic model;
            * request_type: пустая строка;
            * request_data: пустой dict;
        """
        # ==== Mocks ====
        mock_response = Response(messageName="TestResponse")
        mock_response.payload = AssistantResponsePayload(
            pronounceText="some value",
        )
        mock_response.request_type = ""
        mock_response.request_data = {}

        response = await self._run_statemachine(mock_response=mock_response, context_manager_run=context_manager_run)

        assert response[0].name == mock_response.messageName
        assert response[0].request_type is None
        assert response[0].request_data == {}
        assert response[0].payload == mock_response.payload.dict(exclude_none=True)

    @patch("nlpf_statemachine.kit.context_manager.ContextManager.run")
    async def test_run_statemachine_3(self, context_manager_run: MagicMock) -> None:
        """
        ## Тест на запуск стейт-машины с условиями 3.

        Условия:
            * payload: непонятный объект;
            * request_type: None;
            * request_data: pydantic model;
        """

        # ==== Mocks ====
        class RequestData(BaseModel):
            param: str

        mock_response = Response(messageName="TestResponse")
        mock_response.payload = "Some String"
        mock_response.request_type = None
        mock_response.request_data = RequestData(param="param")

        response = await self._run_statemachine(mock_response=mock_response, context_manager_run=context_manager_run)

        assert response[0].name == mock_response.messageName
        assert response[0].request_type is None
        assert response[0].request_data == mock_response.request_data.dict()
        assert response[0].payload == {}

    @patch("nlpf_statemachine.kit.context_manager.ContextManager.run")
    @patch("smart_kit.models.dialogue_manager.DialogueManager.run_scenario")
    async def test_run_scenario_sm_success(self, super_run_scenario: MagicMock, context_manager_run: MagicMock) -> None:
        """
        ## Тест на запуск сценария со стейт-машины с успешным ответом от SM.
        """
        scenario_id: str = random_guid()
        user = self.mocks.user()
        text_preprocessing_result = self.mocks.text_preprocessing_result()
        mock_response = Response(messageName="TestResponse")
        context_manager_run.return_value = mock_response

        # ==== Run ====
        response = await self.core.dialogue_manager.run_scenario(
            scen_id=scenario_id,
            text_preprocessing_result=text_preprocessing_result,
            user=user,
        )

        # ==== Asserts ====
        context_manager_run.assert_called_with(
            event=None,
            message=user.message_pd,
            context=user.context_pd,
            text_preprocessing_result=text_preprocessing_result,
            user=user,
        )
        self._assert_one_command(response)
        assert response[0].name == mock_response.messageName
        assert super_run_scenario.called is False

    @patch("nlpf_statemachine.kit.context_manager.ContextManager.run")
    @patch("smart_kit.models.dialogue_manager.DialogueManager.run_scenario")
    async def test_run_scenario_sm_fail(self, super_run_scenario: MagicMock, context_manager_run: MagicMock) -> None:
        """
        ## Тест на запуск сценария со стейт-машины с отсутствием ответа от SM.
        """
        # ==== Mocks ====
        scenario_id: str = random_guid()
        user = self.mocks.user()
        text_preprocessing_result = self.mocks.text_preprocessing_result()
        context_manager_run.return_value = None
        super_run_scenario.return_value = "Some Value"

        # ==== Run ====
        response = await self.core.dialogue_manager.run_scenario(
            scen_id=scenario_id,
            text_preprocessing_result=text_preprocessing_result,
            user=user,
        )

        # ==== Asserts ====
        context_manager_run.assert_called_with(
            event=None,
            message=user.message_pd,
            context=user.context_pd,
            text_preprocessing_result=text_preprocessing_result,
            user=user,
        )

        super_run_scenario.assert_called_with(
            scen_id=scenario_id,
            text_preprocessing_result=text_preprocessing_result,
            user=user,
        )
        assert response == super_run_scenario.return_value

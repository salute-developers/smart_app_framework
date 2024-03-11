"""
# Пример теста на сервер-экшен и команды.
"""
from random import randint

from nlpf_statemachine.example.app.sc.example_3_server_action_and_commands import SERVER_ACTION_ID
from nlpf_statemachine.example.app.sc.models.commands import EXAMPLE_COMMAND_NAME
from nlpf_statemachine.example.app.sc.models.context import ExampleContext
from nlpf_statemachine.example.app.user import ExampleUser
from tests.nlpf_statemachine_tests.utils import SMTestCase


class TestServerActionAndCommands(SMTestCase):
    """
    # Пример тестирования сервер-экшена и команды.
    """

    CONTEXT_CLASS = ExampleContext
    SMART_KIT_APP_CONFIG = "nlpf_statemachine.example.app_config"
    USER_CLASS = ExampleUser

    async def test_server_action_without_params(self) -> None:
        """
        # Пример сервер-экшена без параметров.
        """
        # ==== Mocks ====
        message = self.mocks.server_action_message(action_id=SERVER_ACTION_ID)

        # ==== Run ====
        await self.run_context_manager_init(
            event=SERVER_ACTION_ID,
            message=message,
        )

        # ==== Asserts ====
        self.assert_debug_info(
            called_event="SERVER_ACTION_ID",
            called_action="CommandOnServerActionExample.example_server_action_handler",
        )
        assert len(self.response.payload.items) == 0

    async def test_server_action_with_params_and_command(self) -> None:
        """
        # Пример сервер-экшена с параметрами и формированием команды в ответе.
        """
        # ==== Mocks ====
        field_1 = str(randint(0, 1000000))
        field_2 = str(randint(0, 1000000))
        message = self.mocks.server_action_message(
            action_id=SERVER_ACTION_ID,
            parameters={"field_1": field_1, "field_2": field_2},
        )

        # ==== Run ====
        await self.run_context_manager_init(
            event=SERVER_ACTION_ID,
            message=message,
        )

        # ==== Asserts ====
        self.assert_debug_info(
            called_event="SERVER_ACTION_ID",
            called_action="CommandOnServerActionExample.example_server_action_handler",
        )

        assert len(self.response.payload.items) == 1

        command = self.response.payload.items[0]
        assert command.command.type == "smart_app_data"
        assert command.command.smart_app_data.command == EXAMPLE_COMMAND_NAME
        assert command.command.smart_app_data.field_1 == field_1
        assert command.command.smart_app_data.field_2 == int(field_2)

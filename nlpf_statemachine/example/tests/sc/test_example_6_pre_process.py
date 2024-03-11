"""
# Пример тестирования пре-процесса.
"""

from nlpf_statemachine.example.app.sc.models.context import ExampleContext
from nlpf_statemachine.example.app.sc.models.message import CustomMessageToSkill, CustomState
from nlpf_statemachine.example.app.user import ExampleUser
from tests.nlpf_statemachine_tests.utils import SMTestCase, random_string


class TestPreProcessIsolatedScenario(SMTestCase):
    """
    # Пример тестирования пре-процесса с использованием изолированого сценария, возвращающего эхо-ответ.
    """

    CONTEXT_CLASS = ExampleContext
    SMART_KIT_APP_CONFIG = "nlpf_statemachine.example.app_config"
    USER_CLASS = ExampleUser

    async def test_pre_process(self) -> None:
        """
        # Тест на пре-процесса с использованием изолированого сценария, возвращающего эхо-ответ.

        В стейте должен находиться параметр `replace_message=True`.

        Returns:
            None.
        """
        # ==== Mock ====
        message = self.mocks.message_to_skill(
            cls=CustomMessageToSkill,
            original_text=random_string(length=50),
            state=CustomState(
                replace_message=True,
            ),
        )

        # ==== Run ====
        await self.run_context_manager_init(
            message=message,
            text_preprocessing_result=self.text_preprocessing_result,
        )

        # ==== Asserts ====
        assert self.response.payload.pronounceText == message.payload.message.original_text

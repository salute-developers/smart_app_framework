"""
# Пример теста на сервер-экшен и команды.
"""
import json
from typing import List, Optional

from nlpf_statemachine.example.app.sc.enums.approve_values import ApproveValues
from nlpf_statemachine.example.app.sc.models.context import ExampleContext
from nlpf_statemachine.example.app.user import ExampleUser
from tests.nlpf_statemachine_tests.utils import SMTestCase


class TestFormAndIntersectionClassifier(SMTestCase):
    """
    # Пример тестирования экшена с формой.
    """

    CONTEXT_CLASS = ExampleContext
    SMART_KIT_APP_CONFIG = "nlpf_statemachine.example.app_config"
    USER_CLASS = ExampleUser

    def _load_tokenized_elements_list(self, prefix: str) -> Optional[List]:
        filename = f"{self.core.app_config.STATIC_PATH}" \
                   f"/tests/tokenized_element_list_example_4_intersection_classifier_{prefix}.json"
        with open(filename, "r") as file:
            return json.load(file)

    async def test_form_with_approve_and_complex_request(self) -> None:
        """
        # Тест на извлечение подтверждения из фразы.

        В нашем кейсе прилетает фраза "заполнение формы: подтверждение".
        В ней имеется как требуемый слот ("подтверждение"), так и лишние слова "заполнение формы".
        Наш кастомный филлер отрабатывает на вхождение слов в строку,
        при этом NLPF ApproveFiller проверяет чёткое совпадение всей строки.

        Поэтому ОР: кастомный филлер отработает, а NLPF ApproveFiller --- нет.
        """
        # ==== Mocks ====
        message = self.mocks.message_to_skill(
            original_text="заполнение формы: подтверждение",
            normalized_text="заполнение форма подтверждение .",
            tokenized_elements_list=self._load_tokenized_elements_list("agreement_complex"),
        )

        # ==== Run ====
        await self.run_context_manager_init(
            message=message,
        )

        # ==== Asserts ====
        self.assert_debug_info(
            called_event="APPROVE",
            called_action="FORM_FILLING_SCENARIO.form_filling_approve_action",
        )
        assert len(self.response.payload.items) == 1
        assert self.response.payload.items[0].command.smart_app_data.custom_approve == ApproveValues.AGREEMENT
        assert self.response.payload.items[0].command.smart_app_data.nlpf_approve is None

    async def test_form_with_approve_and_simple_request(self) -> None:
        """
        # Тест на извлечение подтверждения из фразы двумя слотами и левыми словами.

        В нашем кейсе прилетает фраза "подтверждение".
        В ней имеется **только** требуемый слот ("подтверждение").
        Наш кастомный филлер отрабатывает на вхождение слов в строку,
        а этом NLPF ApproveFiller проверяет чёткое совпадение всей строки.

        Поэтому ОР: оба филлера отработают.
        """
        # ==== Mocks ====
        message = self.mocks.message_to_skill(
            original_text="подтверждение",
            normalized_text="подтверждение .",
            tokenized_elements_list=self._load_tokenized_elements_list("agreement_simple"),
        )

        # ==== Run ====
        await self.run_context_manager_init(
            message=message,
        )

        # ==== Asserts ====
        self.assert_debug_info(
            called_event="APPROVE",
            called_action="FORM_FILLING_SCENARIO.form_filling_approve_action",
        )
        assert len(self.response.payload.items) == 1
        assert self.response.payload.items[0].command.smart_app_data.custom_approve == ApproveValues.AGREEMENT
        assert self.response.payload.items[0].command.smart_app_data.nlpf_approve is True

    async def test_form_with_reject_and_simple_request(self) -> None:
        """
        # Тест на извлечение отрицания из фразы.

        В нашем кейсе прилетает фраза "отрицание".
        В ней имеется **только** требуемый слот ("отрицание").
        Наш кастомный филлер отрабатывает на вхождение слов в строку,
        а этом NLPF ApproveFiller проверяет чёткое совпадение всей строки.

        Поэтому ОР: оба филлера отработают.
        """
        # ==== Mocks ====
        message = self.mocks.message_to_skill(
            original_text="отрицание",
            normalized_text="отрицание .",
            tokenized_elements_list=self._load_tokenized_elements_list("reject_simple"),
        )

        # ==== Run ====
        await self.run_context_manager_init(
            message=message,
        )

        # ==== Asserts ====
        self.assert_debug_info(
            called_event="REJECT",
            called_action="FORM_FILLING_SCENARIO.form_filling_approve_action",
        )
        assert len(self.response.payload.items) == 1
        assert self.response.payload.items[0].command.smart_app_data.custom_approve == ApproveValues.REJECTION
        assert self.response.payload.items[0].command.smart_app_data.nlpf_approve is False

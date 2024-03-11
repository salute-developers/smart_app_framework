"""
# Пример тестов для работы со StaticStorage.
"""
import json
from typing import List, Optional

from nlpf_statemachine.example.app.sc.classifiers.original_text_classifier import Events
from nlpf_statemachine.example.app.sc.models.context import ExampleContext
from nlpf_statemachine.example.app.user import ExampleUser
from nlpf_statemachine.models import AssistantId, EmotionId, PronounceTextType, ResponseMessageName
from tests.nlpf_statemachine_tests.utils import SMTestCase


class ExampleStaticStorage(SMTestCase):
    """
    # Тесты на работу сценария работы со StaticStorage.
    """

    CONTEXT_CLASS = ExampleContext
    SMART_KIT_APP_CONFIG = "nlpf_statemachine.example.app_config"
    USER_CLASS = ExampleUser

    def _load_tokenized_elements_list(self, number: int) -> Optional[List]:
        filename = f"{self.core.app_config.STATIC_PATH}/tests/tokenized_element_list_static_storage_{number}.json"
        with open(filename, "r") as file:
            return json.load(file)

    async def test_1_fix_response(self) -> None:
        """
        ## Кейс 1.

        Фиксированный ответ на верхнем уровне независимо от ассистента.

        Returns:
            None.
        """

        async def _run_character(character_id: AssistantId, tokenized_elements_list: List) -> None:
            # ==== Mock ====
            message = self.mocks.message_to_skill(
                original_text="статичный ответ номер один",
                character_id=character_id,
                tokenized_elements_list=tokenized_elements_list,
            )

            # ==== Run ====
            await self.run_context_manager_init(
                message=message,
                text_preprocessing_result=self.text_preprocessing_result,
            )

            # ==== Asserts ====
            self.assert_debug_info(
                called_event=Events.SIMPLE_ASSISTANT_ANSWER,
                called_action="StaticStorageExample.example_storage_action_1",
                static_code="EXAMPLE_1",
            )
            assert self.response.messageName == ResponseMessageName.ANSWER_TO_USER
            assert len(self.response.payload.pronounceText) > 0
            assert self.response.payload.pronounceTextType == PronounceTextType.SSML
            assert self.response.payload.emotion.emotionId == EmotionId.zhdu_otvet
            assert len(self.response.payload.items) > 0
            assert self.response.payload.intent == "intent_1"
            assert len(self.response.payload.asr_hints.words) == 3

        tok_elements_list = self._load_tokenized_elements_list(number=1)
        await _run_character(character_id=AssistantId.joy, tokenized_elements_list=tok_elements_list)
        await _run_character(character_id=AssistantId.athena, tokenized_elements_list=tok_elements_list)
        await _run_character(character_id=AssistantId.sber, tokenized_elements_list=tok_elements_list)

    async def test_2_different_characters(self) -> None:
        """
        ## Кейс 2.

        Ответ выбирается для соответствующего ассистента (с наличием полей на верхних уровнях)
        с вариативностью ответов.

        Returns:
            None.
        """

        async def _run_character(character_id: AssistantId, tokenized_elements_list: List) -> None:
            # ==== Mock ====
            message = self.mocks.message_to_skill(
                original_text="статичный ответ номер два",
                character_id=character_id,
                tokenized_elements_list=tokenized_elements_list,
            )

            # ==== Run ====
            await self.run_context_manager_init(
                message=message,
                text_preprocessing_result=self.text_preprocessing_result,
            )

            # ==== Asserts ====
            self.assert_debug_info(
                called_event=Events.CHOICE_ASSISTANT_ANSWER,
                called_action="StaticStorageExample.example_storage_action_2",
                static_code="EXAMPLE_2",
            )
            if character_id == AssistantId.joy:
                assert "Джой" in self.response.payload.pronounceText
                assert self.response.payload.pronounceTextType == PronounceTextType.SSML
                assert self.response.payload.emotion.emotionId == EmotionId.oups
            elif character_id == AssistantId.athena:
                assert "Афина" in self.response.payload.pronounceText
                assert self.response.payload.pronounceTextType == PronounceTextType.TEXT
                assert self.response.payload.emotion.emotionId == EmotionId.igrivost
            elif character_id == AssistantId.sber:
                assert "Сбер" in self.response.payload.pronounceText
                assert self.response.payload.pronounceTextType == PronounceTextType.TEXT
                assert self.response.payload.emotion.emotionId == EmotionId.ok_prinyato
            else:
                assert 0 != 1  # wrong assistant!

        tok_elements_list = self._load_tokenized_elements_list(number=2)
        await _run_character(character_id=AssistantId.joy, tokenized_elements_list=tok_elements_list)
        await _run_character(character_id=AssistantId.athena, tokenized_elements_list=tok_elements_list)
        await _run_character(character_id=AssistantId.sber, tokenized_elements_list=tok_elements_list)

    async def test_3_any_character(self) -> None:
        """
        ## Кейс 3.

        Ответ выбирается независимо от асситента (с наличием полей на верхних уровнях)
        и вариативностью ответов для Афины и Сбера.
        Для Джой имеем кастомный ответ.

        Returns:
            None.
        """

        async def _run_character(character_id: AssistantId, tokenized_elements_list: List) -> None:
            # ==== Mock ====
            message = self.mocks.message_to_skill(
                original_text="статичный ответ номер три",
                character_id=character_id,
                tokenized_elements_list=tokenized_elements_list,
            )

            # ==== Run ====
            await self.run_context_manager_init(
                message=message,
                text_preprocessing_result=self.text_preprocessing_result,
            )

            # ==== Asserts ====
            self.assert_debug_info(
                called_event=Events.ANY_ASSISTANT_ANSWER,
                called_action="StaticStorageExample.example_storage_action_3",
                static_code="EXAMPLE_3",
            )
            if character_id == AssistantId.joy:
                assert "Джой" in self.response.payload.pronounceText
                assert self.response.payload.pronounceTextType == PronounceTextType.SSML
                assert self.response.payload.emotion.emotionId == EmotionId.zhdu_otvet
            else:
                assert "для любого ассистента" in self.response.payload.pronounceText
                assert self.response.payload.pronounceTextType == PronounceTextType.TEXT
                assert self.response.payload.emotion.emotionId == EmotionId.ok_prinyato

        tok_elements_list = self._load_tokenized_elements_list(number=3)
        await _run_character(character_id=AssistantId.joy, tokenized_elements_list=tok_elements_list)
        await _run_character(character_id=AssistantId.athena, tokenized_elements_list=tok_elements_list)
        await _run_character(character_id=AssistantId.sber, tokenized_elements_list=tok_elements_list)

    async def test_4_not_duplicate_commands(self) -> None:
        """
        ## Кейс 4.

        Проверяем, что при повторном запуске обработчика с добавлением команды в голосовой ответ, они не дублируются.

        Returns:
            None.
        """

        async def _run_character(character_id: AssistantId, tokenized_elements_list: List) -> None:
            # ==== Mock ====
            message = self.mocks.message_to_skill(
                original_text="статичный ответ номер четыре",
                character_id=character_id,
                tokenized_elements_list=tokenized_elements_list,
            )

            # ==== Run ====
            await self.run_context_manager_init(
                message=message,
                text_preprocessing_result=self.text_preprocessing_result,
            )

            # ==== Asserts ====
            self.assert_debug_info(
                called_event=Events.ANSWER_WITH_COMMAND,
                called_action="StaticStorageExample.example_storage_action_4",
                static_code="EXAMPLE_4",
            )
            assert len(self.response.payload.items) == 1

        tok_elements_list = self._load_tokenized_elements_list(number=4)
        for _ in range(5):
            await _run_character(character_id=AssistantId.joy, tokenized_elements_list=tok_elements_list)

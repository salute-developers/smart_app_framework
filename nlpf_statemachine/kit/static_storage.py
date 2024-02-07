"""
# Общий подход для работы со статикой.
"""

import json
from copy import deepcopy
from random import choice
from typing import Any, Dict, Optional

import yaml

from core.logging.logger_utils import behaviour_log
from nlpf_statemachine.models import (
    ASRHints,
    ASRHintsEOUPhraseMatch,
    AssistantAnswer,
    AssistantId,
    AssistantResponse,
    AssistantResponsePayload,
    Context,
    DebugInfo,
    Emotion,
    FileFormat,
    Response,
    StaticStorage,
    StaticStorageItem,
)


class StaticStorageManager:
    """
    # Менеджер по работе со статикой (для ответов).
    """

    storage: StaticStorage

    def __init__(self, filename: str, file_format: str or FileFormat = FileFormat.YAML) -> None:
        try:
            if file_format == FileFormat.YAML:
                data = self._load_yaml(filename=filename)
            elif file_format == FileFormat.JSON:
                data = self._load_json(filename=filename)
            else:
                data = []
            self.storage = StaticStorage(data=data)

        except Exception as exception:
            behaviour_log(
                f"Exception in static storage initialization with parameters: "
                f"file - {filename}, file_format - {file_format}. Exception: {exception}", level="ERROR", exc_info=True,
            )
            self.storage = StaticStorage()

    @staticmethod
    def _load_yaml(filename: str) -> Dict[str, Any]:
        with open(filename, "r") as file:
            return yaml.safe_load(file)

    @staticmethod
    def _load_json(filename: str) -> Dict[str, Any]:
        with open(filename, "r") as file:
            return json.load(file)

    @staticmethod
    def _merge_payloads(master: AssistantResponsePayload, updater: AssistantResponsePayload) -> \
            AssistantResponsePayload:
        result = AssistantResponsePayload()
        if updater.pronounceText is not None:
            result.pronounceText = updater.pronounceText
        else:
            result.pronounceText = master.pronounceText

        if updater.pronounceTextType is not None:
            result.pronounceTextType = updater.pronounceTextType
        else:
            result.pronounceTextType = master.pronounceTextType

        if updater.emotion and updater.emotion.emotionId:
            result.emotion = Emotion(emotionId=updater.emotion.emotionId)
        elif master.emotion and master.emotion.emotionId:
            result.emotion = Emotion(emotionId=master.emotion.emotionId)

        if updater.auto_listening is not None:
            result.auto_listening = updater.auto_listening
        else:
            result.auto_listening = master.auto_listening

        if updater.intent:
            result.intent = updater.intent
        else:
            result.intent = master.intent

        if updater.finished is not None:
            result.finished = updater.finished
        else:
            result.finished = master.finished

        if updater.asr_hints:
            if not master.asr_hints:
                result.asr_hints = deepcopy(updater.asr_hints)
            else:
                result.asr_hints = ASRHints()
                if updater.asr_hints.words:
                    result.asr_hints.words = updater.asr_hints.words
                else:
                    result.asr_hints.words = master.asr_hints.words

                if updater.asr_hints.enable_letters is not None:
                    result.asr_hints.words = updater.asr_hints.enable_letters
                else:
                    result.asr_hints.words = master.asr_hints.enable_letters

                if updater.asr_hints.nospeechtimeout is not None:
                    result.asr_hints.nospeechtimeout = updater.asr_hints.nospeechtimeout
                else:
                    result.asr_hints.nospeechtimeout = master.asr_hints.nospeechtimeout

                if updater.asr_hints.eou_timeout is not None:
                    result.asr_hints.eou_timeout = updater.asr_hints.eou_timeout
                else:
                    result.asr_hints.eou_timeout = master.asr_hints.eou_timeout

                if updater.asr_hints.eou_phrase_match and updater.asr_hints.eou_phrase_match.regex:
                    result.asr_hints.eou_phrase_match = ASRHintsEOUPhraseMatch()
                    result.asr_hints.eou_phrase_match.regex = updater.asr_hints.eou_phrase_match.regex

                elif master.asr_hints.eou_phrase_match and master.asr_hints.eou_phrase_match.regex:
                    result.asr_hints.eou_phrase_match = ASRHintsEOUPhraseMatch()
                    result.asr_hints.eou_phrase_match.regex = master.asr_hints.eou_phrase_match.regex

        elif master.asr_hints:
            result.asr_hints = deepcopy(master.asr_hints)

        if updater.suggestions:
            result.suggestions = updater.suggestions
        else:
            result.suggestions = master.suggestions

        if updater.items:
            result.items = updater.items
        else:
            result.items = master.items

        return result

    def _get_answer(self, assistant_answer: AssistantAnswer) -> AssistantResponsePayload:
        if assistant_answer.answers:
            answer = choice(assistant_answer.answers)
            return self._merge_payloads(assistant_answer, answer)
        return AssistantResponsePayload(**assistant_answer.model_dump())

    def _get_assistant_payload(self, data: StaticStorageItem, character_id: Optional[str]) -> \
            Optional[AssistantResponsePayload]:
        if character_id:
            if character_id == AssistantId.joy and data.joy:
                return self._merge_payloads(master=data, updater=self._get_answer(data.joy))
            if character_id == AssistantId.athena and data.athena:
                return self._merge_payloads(master=data, updater=self._get_answer(data.athena))
            if character_id == AssistantId.sber and data.sber:
                return self._merge_payloads(master=data, updater=self._get_answer(data.sber))
        if data.any:
            return self._merge_payloads(master=data, updater=self._get_answer(data.any))
        return AssistantResponsePayload(**data.model_dump())

    def response(self, code: str, context: Context = None, activate_app_info: bool = True) -> Optional[Response]:
        """
        # Общий метод, формирующий ответ.

        Args:
            code (str): Код, по которому сформируется ответ;
            context (Context): Текущий контекст.
            activate_app_info (bool): Флаг запуска приложения.

        Returns:
            Response
        """
        if not self.storage or code not in self.storage.data:
            return

        if context:
            character_id = context.local.character_id
        else:
            character_id = None

        payload = self._get_assistant_payload(data=deepcopy(self.storage.data[code]), character_id=character_id)
        if not activate_app_info:
            payload.activate_app_info = activate_app_info
        response = AssistantResponse(payload=payload, debug_info=DebugInfo(static_code=code))
        return response

    def answer_to_user(self, code: str, context: Context = None, activate_app_info: bool = True) -> \
            Optional[AssistantResponse]:
        """
        # Формирование сообщения ANSWER_TO_USER.

        Args:
            code (str): Код, по которому сформируется ответ;
            context (Context): Текущий контекст.
            activate_app_info (bool): Флаг запуска приложения.

        Returns:
            Response
        """
        return self.response(code=code, context=context, activate_app_info=activate_app_info)

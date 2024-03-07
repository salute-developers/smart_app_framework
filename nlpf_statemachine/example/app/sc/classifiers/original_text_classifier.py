"""
# Пример простого классификатора (анализ запроса).
"""

from typing import Dict, Optional

from core.text_preprocessing.constants import NUM_TOKEN
from nlpf_statemachine.example.const import STATIC_PARAPHRASE
from nlpf_statemachine.kit import Classifier
from nlpf_statemachine.models import Context, MessageToSkill, SmartEnum


class Events(SmartEnum):
    """
    # Список возможных событий.

    События соответствуют конкретным кейсам в примере:

    1. Фиксированный ответ на верхнем уровне в static-файле;
    2. Ответ для соответствующего ассистента;
    3. Ответ для любого ассистента;
    4. Ответ с добавлением простой команды.
    """

    SIMPLE_ASSISTANT_ANSWER = "SIMPLE_ASSISTANT_ANSWER"
    CHOICE_ASSISTANT_ANSWER = "CHOICE_ASSISTANT_ANSWER"
    ANY_ASSISTANT_ANSWER = "ANY_ASSISTANT_ANSWER"
    ANSWER_WITH_COMMAND = "ANSWER_WITH_COMMAND"


class OriginalTextClassifier(Classifier):
    """
    # Пример простого классификатора.

    Данный классификатор проверяет наличие слова в запросе.
    """

    def run(self, message: MessageToSkill, context: Context, form: Dict) -> Optional[str]:
        """
        ## Запуск классификации.

        *Основной метод для переопределения*.

        Args:
            message (nlpf_statemachine.models.message.protocol.assistant_message.BaseMessage): Тело запроса.
            context (nlpf_statemachine.models.context.Context): Контекст.
            form (Dict[str, Any]): Форма

        Returns:
            str: результат классификации (event).
        """
        if STATIC_PARAPHRASE in message.payload.message.original_text:
            for token in message.payload.message.tokenized_elements_list:
                if token.get("token_type") == NUM_TOKEN:
                    text = token.get("text")
                    if text == "1":
                        return Events.SIMPLE_ASSISTANT_ANSWER
                    elif text == "2":
                        return Events.CHOICE_ASSISTANT_ANSWER
                    elif text == "3":
                        return Events.ANY_ASSISTANT_ANSWER
                    elif text == "4":
                        return Events.ANSWER_WITH_COMMAND

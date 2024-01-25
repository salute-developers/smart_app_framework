"""
# Пример простого классификатора (анализ запроса).
"""

from typing import Dict, Optional

from nlpf_statemachine.kit import Classifier
from nlpf_statemachine.models import Context, MessageToSkill, SmartEnum

STATIC_PARAPHRASE = "статичный ответ"
NUM_TOKEN = "NUM_TOKEN"


class Events(SmartEnum):
    """
    # Список возможных событий.

    События соответствуют конкретным кейсам в примере:

    1. Фиксированный ответ на верхнем уровне в static-файле;
    2. Ответ для соответствующего ассистента;
    3. Ответ для любого ассистента;
    """

    STATIC_STORAGE_EVENT_1 = "STATIC_STORAGE_EVENT_1"
    STATIC_STORAGE_EVENT_2 = "STATIC_STORAGE_EVENT_2"
    STATIC_STORAGE_EVENT_3 = "STATIC_STORAGE_EVENT_3"
    STATIC_STORAGE_EVENT_4 = "STATIC_STORAGE_EVENT_4"


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
                        return Events.STATIC_STORAGE_EVENT_1
                    elif text == "2":
                        return Events.STATIC_STORAGE_EVENT_2
                    elif text == "3":
                        return Events.STATIC_STORAGE_EVENT_3
                    elif text == "4":
                        return Events.STATIC_STORAGE_EVENT_4

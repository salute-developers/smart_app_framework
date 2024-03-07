"""
# ApproveFiller для примера #4.
"""
from nlpf_statemachine.example.app.sc.enums.approve_values import ApproveValues
from nlpf_statemachine.kit import Filler
from nlpf_statemachine.models import Context, MessageToSkill

# Определяем фразы, которые хотим использовать для подтверждения и отрицания.
# Хорошей практикой является определение их в статичных-файлах.
yes_words = ["да", "подтверждаю", "так точно", "согласен", "подтверждение"]
no_words = ["нет", "не согласен", "отрицание"]


class CustomApproveFiller(Filler):
    """
    # Пример филлера.
    """

    def run(self, message: MessageToSkill, context: Context) -> ApproveValues:
        """
        # Запуск филлера.

        Args:
            message (nlpf_statemachine.models.message.protocol.assistant_message.MessageToSkill): Тело запроса.
            context (nlpf_statemachine.models.context.Context): Контекст.

        Returns:
            ApproveValues: значение подтверждения или отрицания, извлечённое из запроса.
        """
        for word in yes_words:
            if word in message.payload.message.original_text:
                return ApproveValues.AGREEMENT

        for word in no_words:
            if word in message.payload.message.original_text:
                return ApproveValues.REJECTION

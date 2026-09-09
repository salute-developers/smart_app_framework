"""
# Пример User.

Для работы проекта необходимо относледовать свой `User` от базового класса
`nlpf_statemachine.override.user.SMUser`.
"""
from nlpf_statemachine.example.app.sc.enums.integration_message_names import IntegrationResponseMessageName
from nlpf_statemachine.example.app.sc.models.context import ExampleContext
from nlpf_statemachine.example.app.sc.models.message import CustomAssistantMessageServerAction, CustomMessageToSkill
from nlpf_statemachine.example.app.sc.models.integration import GetDataResponse
from nlpf_statemachine.models import BaseMessage, RequestMessageName
from nlpf_statemachine.override import SMUser


class ExampleUser(SMUser):
    """
    # Переопределение User для проекта.
    """

    @property
    def message_models(self) -> dict[str, list[type[BaseMessage]]]:
        """
        ## Определение моделей запросов.

        *Объекты строятся последовательно!*
        Если объект построился (прошла валидация всех полей) --- успех.
        Иначе строится следующий объект.
        """
        models = super().message_models
        models[RequestMessageName.MESSAGE_TO_SKILL] = [CustomMessageToSkill]
        models[RequestMessageName.SERVER_ACTION] = [CustomAssistantMessageServerAction]
        models[IntegrationResponseMessageName.GENERATE_DATA] = [GetDataResponse]
        return models

    @property
    def context_model(self) -> type[ExampleContext]:
        """
        ## Определение модели для контекста.
        """
        return ExampleContext

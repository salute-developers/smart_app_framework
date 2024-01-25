"""
# Пример SmartAppResources.

Для работы проекта необходимо относледовать свой `SmartAppResources` от базового класса
`nlpf_statemachine.override.model_config.SMSmartAppResources`.
И указать в параметре CONTEXT_MANAGER ссылку на инстанс вашего ContextManager.
"""
from nlpf_statemachine.example.app.context_manager import context_manager
from nlpf_statemachine.override.model_config import SMSmartAppResources


class ExampleResources(SMSmartAppResources):
    """
    # Переопределение SmartAppResources для проекта.
    """

    CONTEXT_MANAGER = context_manager

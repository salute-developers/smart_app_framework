"""Описание моделей для интеграций."""
from nlpf_statemachine.models import SmartEnum


class IntegrationRequestMessageName(SmartEnum):
    """Список наименований запросов в интеграцию."""

    GENERATE_DATA = "GENERATE_DATA_REQUEST"


class IntegrationResponseMessageName(SmartEnum):
    """Список наименований ответов от интеграции."""

    GENERATE_DATA = "GENERATE_DATA_RESPONSE"

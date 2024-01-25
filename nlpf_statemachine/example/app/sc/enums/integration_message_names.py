"""Описание моделей для интеграций."""
from nlpf_statemachine.models import SmartEnum


class IntegrationRequestMessageName(SmartEnum):
    """Список наименований запросов интеграцию."""

    GENERATE_TOKEN = "ECOM_GENERATE_TOKEN_REQUEST"


class IntegrationResponseMessageName(SmartEnum):
    """Список наименований ответов от интеграции."""

    GENERATE_TOKEN = "ECOM_GENERATE_TOKEN_RESPONSE"

"""
# Описание конфигов.

Конфиги можно настраивать в своём проекте через переменные окружения.
"""
from decouple import config

from nlpf_statemachine.models.enums import ResponseMessageName


class SMConfig:
    default_integration_behaviour_id = config("DEFAULT_INTEGRATION_BEHAVIOR_ID", cast=str, default="nlpf_statemachine")
    transaction_timeout = config("TRANSACTION_TIMEOUT", cast=int, default=10)
    transaction_massage_name_finish_list = config(
        "TRANSACTION_MESSAGE_NAME_FINISH_LIST",
        cast=lambda scenarios: [
            message_name.strip() for message_name in scenarios.split(",")
        ],
        default=", ".join(list(ResponseMessageName)),
    )

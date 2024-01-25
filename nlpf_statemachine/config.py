"""
# Описание конфигов.

Конфиги можно настраивать в своём проекте через переменные окружения.
"""
from decouple import config

# ==== Base ====
# Время в секундах, после котрых транзакция протухает
from nlpf_statemachine.models.enums import ResponseMessageName

SCREEN_FIELD_NAME = config("SCREEN_FIELD_NAME", cast=str, default="screen")
DEFAULT_INTEGRATION_BEHAVIOR_ID = config("DEFAULT_INTEGRATION_BEHAVIOR_ID", cast=str, default="nlpf_statemachine")

# ==== Transactions Configs ====
# Время в секундах, после котрых транзакция протухает
TRANSACTION_TIMEOUT = config("TRANSACTION_TIMEOUT", cast=int, default=10)

# MessageNames, которые заканчивают транзакцию
TRANSACTION_MESSAGE_NAME_FINISH_LIST = config(
    "TRANSACTION_MESSAGE_NAME_FINISH_LIST",
    cast=lambda scenarios: [
        message_name.strip() for message_name in scenarios.split(",")
    ],
    default=", ".join(list(ResponseMessageName)),
)

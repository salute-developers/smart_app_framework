"""
# Общие константы, удобные для использования.

1. Список всех ассистентов: AssistantJoy, AssistantAthena, AssistantSber.
"""

from nlpf_statemachine.models import AssistantAppeal, AssistantGender, AssistantId, AssistantName, Character

AssistantJoy = Character(
    id=AssistantId.joy,
    name=AssistantName.joy,
    gender=AssistantGender.male,
    appeal=AssistantAppeal.no_official,
)

AssistantAthena = Character(
    id=AssistantId.athena,
    name=AssistantName.athena,
    gender=AssistantGender.female,
    appeal=AssistantAppeal.official,
)

AssistantSber = Character(
    id=AssistantId.sber,
    name=AssistantName.sber,
    gender=AssistantGender.male,
    appeal=AssistantAppeal.official,
)

CONTEXT_MANAGER_ID = "StateMachineScenarios"
DEFAULT = "DEFAULT"
DEFAULT_ACTION = "DEFAULT_ACTION"
GLOBAL_NODE_NAME = "GLOBAL_NODE"
INTEGRATION_TIMEOUT = 5
STATE_MACHINE_REPOSITORY_NAME = "StateMachineScenarios"

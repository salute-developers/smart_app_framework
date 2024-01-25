"""
# Список возможных значений филлера из примера #4.
"""
from nlpf_statemachine.models import SmartEnum


class ApproveValues(SmartEnum):
    """
    # Возможные значения слота Approve Filler.
    """

    AGREEMENT = "AGREEMENT"
    REJECTION = "REJECTION"

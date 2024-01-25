"""
# Возможные стратегии смартапа.
"""

from typing import Optional

from pydantic import BaseModel


class Strategies(BaseModel):
    """
    # Описание модели Strategies.
    """

    happy_birthday: Optional[bool]
    """Сообщает, что у пользователя сегодня день рождения."""
    last_call: Optional[str]
    """Время, которое прошло с момента последнего обращения к смартапу."""
    is_alice: Optional[bool]
    """
    Передается только в том случае, когда биометрия определила голос Яндекс Алисы.
    В остальных случаях поле отсутствует.
    """

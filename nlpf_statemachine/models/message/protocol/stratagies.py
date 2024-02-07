"""
# Возможные стратегии смартапа.
"""

from pydantic import BaseModel, Field


class Strategies(BaseModel):
    """
    # Описание модели Strategies.
    """

    happy_birthday: bool | None = Field(default=None)
    """Сообщает, что у пользователя сегодня день рождения."""
    last_call: bool | None = Field(default=None)
    """Время, которое прошло с момента последнего обращения к смартапу."""
    is_alice: bool | None = Field(default=None)
    """
    Передается только в том случае, когда биометрия определила голос Яндекс Алисы.
    В остальных случаях поле отсутствует.
    """

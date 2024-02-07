"""
# Составной идентификатор пользователя.
"""

from pydantic import BaseModel, Field


class UUID(BaseModel):
    """
    # Описание модели UUID.

    Составной идентификатор пользователя, от которого пришёл запрос.
    """

    sub: str | None = Field(default=None)
    """
    Постоянный идентификатор пользователя, созданный на основе SberID.
    Может отсутствовать, если пользователь не аутентифицирован
    """
    userId: str | None = Field(default=None)
    """Id пользователя."""
    userChannel: str | None = Field(default=None)
    """Идентификатор канала коммуникации"""
    sid: str | None = Field(default=None)
    """Сквозной идентификатор пользователя"""
    uuid_sberid: str | None = Field(default=None)
    """Единый идентификатор пользователя от СберИд"""

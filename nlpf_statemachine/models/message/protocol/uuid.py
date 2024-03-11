"""
# Составной идентификатор пользователя.
"""

from typing import Optional

from pydantic import BaseModel, Field


class UUID(BaseModel):
    """
    # Описание модели UUID.

    Составной идентификатор пользователя, от которого пришёл запрос.
    """

    sub: Optional[str] = Field(default=None)
    """
    Постоянный идентификатор пользователя, созданный на основе SberID.
    Может отсутствовать, если пользователь не аутентифицирован
    """
    userId: Optional[str] = Field(default=None)
    """Id пользователя."""
    userChannel: Optional[str] = Field(default=None)
    """Идентификатор канала коммуникации"""
    sid: Optional[str] = Field(default=None)
    """Сквозной идентификатор пользователя"""
    uuid_sberid: Optional[str] = Field(default=None)
    """Единый идентификатор пользователя от СберИд"""

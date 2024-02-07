"""
# Базовая модель любого запроса в сервис.
"""

from pydantic import BaseModel, Field

from .uuid import UUID


class BaseMessage(BaseModel):
    """
    # Описание модели BaseMessage.
    """

    messageName: str
    """Тип сообщения. Определяет логику обработки события."""
    messageId: int | None = Field(default=None)
    """
    Идентификатор запроса, который отправил ассистент.
    Ответ на запрос должен содержать такой же идентификатор в поле messageId.
    """
    sessionId: str | None = Field(default=None)
    """
    Идентификатор соединения платформы (не диалоговой сессии).
    128 bit hex GUID converted to string.
    """
    uuid: UUID | None = Field(default=None)
    "Составной идентификатор пользователя."
    payload: dict | None = Field(default={})
    """Коллекция, в которой в зависимости от потребителя и messageName передается дополнительная информация."""

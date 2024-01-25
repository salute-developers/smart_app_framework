"""
# Базовая модель любого запроса в сервис.
"""
from typing import Dict, Optional

from pydantic import BaseModel

from .uuid import UUID


class BaseMessage(BaseModel):
    """
    # Описание модели BaseMessage.
    """

    messageName: str
    """Тип сообщения. Определяет логику обработки события."""
    messageId: Optional[int]
    """
    Идентификатор запроса, который отправил ассистент.
    Ответ на запрос должен содержать такой же идентификатор в поле messageId.
    """
    sessionId: Optional[str]
    """
    Идентификатор соединения платформы (не диалоговой сессии).
    128 bit hex GUID converted to string.
    """
    uuid: Optional[UUID]
    "Составной идентификатор пользователя."

    payload: Optional[Dict] = {}
    """Коллекция, в которой в зависимости от потребителя и messageName передается дополнительная информация."""

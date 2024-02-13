"""
# Описание модели конфигурации данных для запроса в интеграцию.
"""
from typing import Optional

from pydantic import BaseModel, Field


class RequestData(BaseModel):
    """
    # Данные для запроса в кафку.
    """

    topic_key: Optional[str] = Field(default=None)
    """Ключ кафки для запроса"""
    kafka_replyTopic: Optional[str] = Field(default=None)
    """Ключ кафки для ответа"""
    app_callback_id: Optional[str] = Field(default=None)
    """ID бихейвора"""

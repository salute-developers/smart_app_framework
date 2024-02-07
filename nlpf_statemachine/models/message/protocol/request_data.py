"""
# Описание модели конфигурации данных для запроса в интеграцию.
"""

from pydantic import BaseModel, Field


class RequestData(BaseModel):
    """
    # Данные для запроса в кафку.
    """

    topic_key: str | None = Field(default=None)
    """Ключ кафки для запроса"""
    kafka_replyTopic: str | None = Field(default=None)
    """Ключ кафки для ответа"""
    app_callback_id: str | None = Field(default=None)
    """ID бихейвора"""

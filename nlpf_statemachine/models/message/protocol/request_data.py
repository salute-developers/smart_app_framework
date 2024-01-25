"""
# Описание модели конфигурации данных для запроса в интеграцию.
"""

from typing import Optional

from pydantic import BaseModel


class RequestData(BaseModel):
    """
    # Данные для запроса в кафку.
    """

    topic_key: Optional[str]
    """Ключ кафки для запроса"""
    kafka_replyTopic: Optional[str]
    """Ключ кафки для ответа"""
    app_callback_id: Optional[str]
    """ID бихейвора"""

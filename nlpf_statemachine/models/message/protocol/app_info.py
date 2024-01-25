"""
Информация о смартапе.
"""
from typing import Optional, Dict, Any

from pydantic import BaseModel, Field


class AppInfo(BaseModel):
    """
    # Описание модели AppInfo.
    """

    projectId: Optional[str]
    """Идентификатор проекта в SmartMarket Studio."""
    frontendType: Optional[str]
    """Тип смартапа."""
    applicationId: Optional[str]
    """Идентификатор смартапа."""
    appversionId: Optional[str] = Field(description="Идентификатор опубликованной версии смартапа.")
    """Идентификатор опубликованной версии смартапа."""
    frontendEndpoint: Optional[str]
    """Ссылка на веб-приложение. Поле актуально для Canvas Apps."""
    systemName: Optional[str]
    """Более читаемый аналог поля projectId.Не актуален для внешних приложений."""
    frontendStateId: Optional[str]
    """Объединённое значение полей projectId, applicationId и appversionId."""
    apkInfo: Optional[Dict[str, Any]]
    """Информация о приложении"""
    ageLimit: Optional[int]
    """Информация о возрастном ограничении"""
    affiliationType: Optional[str]
    """Тип перехода"""

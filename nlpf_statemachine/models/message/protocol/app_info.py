"""
Информация о смартапе.
"""

from typing import Optional, Dict

from pydantic import BaseModel, Field


class AppInfo(BaseModel):
    """
    # Описание модели AppInfo.
    """

    projectId: Optional[str] = Field(default=None)
    """Идентификатор проекта в SmartMarket Studio."""
    frontendType: Optional[str] = Field(default=None)
    """Тип смартапа."""
    applicationId: Optional[str] = Field(default=None)
    """Идентификатор смартапа."""
    appversionId: Optional[str] = Field(default=None)
    """Идентификатор опубликованной версии смартапа."""
    frontendEndpoint: Optional[str] = Field(default=None)
    """Ссылка на веб-приложение. Поле актуально для Canvas Apps."""
    systemName: Optional[str] = Field(default=None)
    """Более читаемый аналог поля projectId.Не актуален для внешних приложений."""
    frontendStateId: Optional[str] = Field(default=None)
    """Объединённое значение полей projectId, applicationId и appversionId."""
    apkInfo: Optional[Dict] = Field(default=None)
    """Информация о приложении"""
    ageLimit: Optional[int] = Field(default=None)
    """Информация о возрастном ограничении"""
    affiliationType: Optional[str] = Field(default=None)
    """Тип перехода"""

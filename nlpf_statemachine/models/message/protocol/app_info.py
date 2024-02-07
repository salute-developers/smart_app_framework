"""
Информация о смартапе.
"""

from pydantic import BaseModel, Field


class AppInfo(BaseModel):
    """
    # Описание модели AppInfo.
    """

    projectId: str | None = Field(default=None)
    """Идентификатор проекта в SmartMarket Studio."""
    frontendType: str | None = Field(default=None)
    """Тип смартапа."""
    applicationId: str | None = Field(default=None)
    """Идентификатор смартапа."""
    appversionId: str | None = Field(default=None)
    """Идентификатор опубликованной версии смартапа."""
    frontendEndpoint: str | None = Field(default=None)
    """Ссылка на веб-приложение. Поле актуально для Canvas Apps."""
    systemName: str | None = Field(default=None)
    """Более читаемый аналог поля projectId.Не актуален для внешних приложений."""
    frontendStateId: str | None = Field(default=None)
    """Объединённое значение полей projectId, applicationId и appversionId."""
    apkInfo: dict | None = Field(default=None)
    """Информация о приложении"""
    ageLimit: int | None = Field(default=None)
    """Информация о возрастном ограничении"""
    affiliationType: str | None = Field(default=None)
    """Тип перехода"""

from typing import List
from functools import cached_property

from core.model.field import Field
from scenarios.user.user_model import User

from app.user.parametrizer import CustomParametrizer


class CustomUser(User):
    """Модель для хранения данных конкретного пользователя

    Для использования данного пользователя присвойте переменной USER в app_config этот класс как значение.
    """
    def __init__(self, id, message, db_data, settings, descriptions, parametrizer_cls, load_error=False):
        super().__init__(id, message, db_data, settings, descriptions, parametrizer_cls, load_error)

    @property
    def fields(self) -> List[Field]:
        """Возвращает список полей с данными пользователя"""
        return super().fields + []

    @cached_property
    def parametrizer(self):
        return CustomParametrizer(self, {})

    def expire(self):
        super().expire()

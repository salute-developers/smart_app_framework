"""
# Модели для описания фиче-лаунчера.
"""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel


class PublicFL(BaseModel):
    """
    # Общая коллекция флагов, которые предназначены для всех сервисов/навыков.
    """

    greenfield_segment_list: Optional[List[str]]
    """Список сегментов GF к которым принадлежит пользователь"""
    greenfield_percentage: Optional[int]
    """
    Процент раскатки который рассчитан для пользователя по формуле:
    user_id = uid.encode('utf-8')
    hash = int(hashlib.sha256(user_id).hexdigest(), 16)
    res = hash % 100
    """


class FeatureLauncher(BaseModel):
    """
    # Модель фиче лончера.
    """

    assigned_testing_groups: Optional[List[str]]
    """Список групп тестирования в которые попал пользователь"""
    public: Optional[PublicFL]
    """Общая коллекция флагов, которые предназначены для всех сервисов/навыков"""
    nlp_platform: Optional[Dict[str, Any]]
    """Общая секция"""

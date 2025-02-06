from __future__ import annotations

import time
from typing import TYPE_CHECKING, Any

from core.basic_models.variables.variables import Variables

if TYPE_CHECKING:
    from scenarios.user.user_model import User


class MidVariables(Variables):
    def __init__(self, items: dict | None, user: User, savable: bool = True):
        super().__init__(items=items, user=user, savable=savable)
        self.DEFAULT_TTL = user.settings["template_settings"].get("vps_waiting_timeout", 20000) / 1000
        self._user = user

    def get(self, key: Any, default: Any = None) -> Any:
        return super().get(key=str(self._user.message.incremental_id), default={}).get(key, default)

    def update(self, key: Any, value: Any, ttl: int | None = None) -> None:
        mid = str(self._user.message.incremental_id)
        mid_variable, old_expire_time = self._storage.get(mid, ({}, self.DEFAULT_TTL + time.time()))
        mid_variable[key] = value
        self._storage[mid] = mid_variable, ttl + time.time() if ttl else old_expire_time

    def delete_mid_variables(self) -> None:
        del self._storage[str(self._user.message.incremental_id)]

    def set(self, key, value, ttl=None):
        raise NotImplementedError

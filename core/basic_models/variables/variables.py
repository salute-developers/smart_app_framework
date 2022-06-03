import time
from typing import Dict, Any, Optional


class Variables:
    DEFAULT_TTL = 86400

    def __init__(self, items, user, savable: bool = True):
        self._savable = savable
        self._storage: Dict[str, Any] = items or {}

    @property
    def raw(self) -> Optional[Dict[str, Any]]:
        if self._savable:
            return self._storage
        return None

    @property
    def values(self) -> Dict[str, Any]:
        self.expire()
        result = {}
        for key in self._storage:
            value, _ = self._storage[key]
            result[key] = value
        return result

    def set(self, key, value, ttl=None) -> None:
        ttl = ttl if ttl is not None else self.DEFAULT_TTL
        self._storage[key] = value, time.time() + ttl

    def update(self, key, value, ttl=None) -> None:
        _, old_ttl = self._storage[key]
        ttl = ttl or old_ttl
        self.set(key, value, ttl)

    def get(self, key, default=None):
        value, expire_time = self._storage.get(key, (default, time.time() + self.DEFAULT_TTL))
        if expire_time <= time.time():
            value = default
        return value

    def expire(self) -> None:
        for key in list(self._storage):
            _, expire_time = self._storage[key]
            if expire_time <= time.time():
                self.delete(key)

    def delete(self, key) -> None:
        del self._storage[key]

    def clear(self) -> None:
        self._storage.clear()

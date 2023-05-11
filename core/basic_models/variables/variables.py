import time
from typing import Dict, Any, Optional, Tuple


class Variables:
    DEFAULT_TTL = 86400

    def __init__(self, items, user, savable: bool = True):
        self._savable = savable
        self._storage: Dict[str, Tuple[Any, float]] = items or {}

    @property
    def raw(self) -> Optional[Dict[str, Any]]:
        if self._savable:
            return self._storage
        return None

    @property
    def values(self) -> Dict[str, Any]:
        self.expire()
        return {key: value[0] for key, value in self._storage.items()}

    def set(self, key, value, ttl=None) -> None:
        ttl = ttl if ttl is not None else self.DEFAULT_TTL
        self._storage[key] = value, time.time() + ttl

    def update(self, key, value, ttl=None) -> None:
        _, expire_time = self._storage.get(key, (None, None))
        if not expire_time:
            ttl = ttl if ttl is not None else self.DEFAULT_TTL
            expire_time = ttl + time.time()
        self._storage[key] = value, expire_time

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

from __future__ import annotations
import timeit
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from scenarios.user.user_model import User


class StatsTimer:
    def __init__(self, add_to_inner_stats: bool = False, user: User | None = None, system: str | None = None):
        self._add_to_inner_stats = add_to_inner_stats
        self._user = user
        self._system = system

    def __enter__(self):
        if self._add_to_inner_stats:
            self._initial_inner_stats_count = len(self._user.variables.get(
                key=f"{self._user.message.incremental_id}inner_stats", default=[]
            ))
        self.start = timeit.default_timer()
        return self

    def __exit__(self, *args):
        self.end = timeit.default_timer()
        self.secs = self.end - self.start
        self.msecs = self.secs * 1000
        if self._add_to_inner_stats:
            inner_key = f"{self._user.message.incremental_id}inner_stats"
            user_time = self.msecs - inner_stats_time_sum(
                self._user.variables.get(key=inner_key, default=[])[self._initial_inner_stats_count:]
            )
            s_key = f"{self._user.message.incremental_id}script_time_ms"
            self._user.variables.set(key=s_key, value=self._user.variables.get(key=s_key, default=0) - user_time,
                                     ttl=20)
            self._user.variables.set(key=inner_key, ttl=20, value=self._user.variables.get(key=inner_key, default=[]) +
                                                                  [{
                                                                      "system": self._system,
                                                                      "inner_stats": [],
                                                                      "time": user_time,
                                                                      "version": None,
                                                                  }])


def inner_stats_time_sum(inner_stats: list[dict[str, Any]]) -> float:
    return sum(inner_stats_time_sum(stat.get("inner_stats")) + stat["time"] for stat in inner_stats)

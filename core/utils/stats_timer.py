from __future__ import annotations
import timeit
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from scenarios.user.user_model import User


class StatsTimer:
    def __init__(self, system: str | None = None, user: User | None = None):
        self.stats: Stats | None = None
        self._system = system
        self._user = user

    def __enter__(self):
        self.start = timeit.default_timer()
        if self._system:
            self._initial_inner_stats_count = len(self._user.mid_variables.get(
                key=f"inner_stats", default=[]
            ))
        return self

    def __exit__(self, *args):
        self.end = timeit.default_timer()
        self.secs = self.end - self.start
        self.msecs = self.secs * 1000
        if self._system:
            self.stats = Stats(system=self._system, time=self.msecs - inner_stats_time_sum(
                self._user.mid_variables.get(key="inner_stats", default=[])[self._initial_inner_stats_count:]
            ))
            self._user.mid_variables.update(
                key="inner_stats",
                value=self._user.mid_variables.get(key="inner_stats", default=[]) + [self.stats]
            )


class Stats:
    def __init__(self, time: float, system: str, version: str | None = None,
                 inner_stats: list[Stats] | None = None):
        self.system = system
        self.version = version
        self._inner_stats: list[Stats] = inner_stats or []
        self._time = time
        self._inner_stats_time_sum = None

    @property
    def time(self) -> float:
        return self._time - self.inner_stats_time_sum

    def set_inner_stats(self, inner_stats: list[Stats]) -> None:
        self._inner_stats = inner_stats
        self._inner_stats_time_sum = None

    @property
    def inner_stats_time_sum(self) -> float:
        if self._inner_stats_time_sum is None:
            self._inner_stats_time_sum = inner_stats_time_sum(self._inner_stats)
        return self._inner_stats_time_sum

    def toJSON(self) -> dict[str, Any]:
        return {
            "system": self.system,
            "inner_stats": [stat.toJSON() for stat in self._inner_stats],
            "time": self.time,
            "version": self.version,
        }


def inner_stats_time_sum(inner_stats: list[Stats]) -> float:
    return sum(stat.time + stat.inner_stats_time_sum for stat in inner_stats)

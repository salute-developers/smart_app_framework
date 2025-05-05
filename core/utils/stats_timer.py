from __future__ import annotations

import time
import timeit
from collections.abc import Iterable
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
            self.start_ts = time.time()
        return self

    def __exit__(self, *args):
        self.end = timeit.default_timer()
        self.secs = self.end - self.start
        self.msecs = self.secs * 1000
        if self._system:
            self.stats = Stats(system=self._system, time=self.msecs, start_ts=self.start_ts,
                               finish_ts=time.time())
            self._user.mid_variables.update(
                key="inner_stats",
                value=self._user.mid_variables.get(key="inner_stats", default=[]) + [self.stats]
            )


class Stats:
    def __init__(self, start_ts: float | None = None, finish_ts: float | None = None, time: float | None = None,
                 system: str | None = None, version: str | None = None,
                 inner_stats: Iterable[Stats | dict[str, Any]] = (), optional: dict | None = None, **kwargs):
        self.system = system
        self.version = version
        self.optional = optional
        self.start_ts = start_ts
        self.finish_ts = finish_ts
        self.time = time or ((start_ts - finish_ts) if start_ts and finish_ts else None)
        self._inner_stats: list[Stats] = [
            stats if isinstance(stats, Stats) else Stats(**stats)
            for stats in inner_stats
        ]

    def add_inner_stats(self, stats: dict[str, Any], copy_system: bool = True, copy_version: bool = True) -> None:
        self._inner_stats = [Stats(**stats)]
        self.system = (stats.get("system") if copy_system else None) or self.system
        self.version = (stats.get("version") if copy_version else None) or self.version

    def toJSON(self) -> dict[str, Any]:
        return {
            "system": self.system,
            "version": self.version,
            "time": self.time,
            "start_ts": self.start_ts,
            "finish_ts": self.finish_ts,
            "optional": self.optional,
            "inner_stats": [stats.toJSON() for stats in self._inner_stats],
        }

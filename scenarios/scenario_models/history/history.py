from __future__ import annotations

from time import time
from typing import Any, NamedTuple, TYPE_CHECKING

from core.logging.logger_utils import log

if TYPE_CHECKING:
    from scenarios.scenario_models.history import HistoryDescription
    from scenarios.user.user_model import User


class Event(NamedTuple):
    type: str | None = None
    scenario: str | None = None
    scenario_version: str | None = None
    node: str | None = None
    result: str | None = None
    content: dict[str, str] | None = None
    created_time: float = time()

    def to_dict(self) -> dict[str, Any]:
        return self._asdict()


class History:

    _events: list[Event]
    _description: 'HistoryDescription'

    def __init__(self, items: dict[str, Any], description: 'HistoryDescription', user: 'User'):
        items = items or {}
        self._description = description
        self._events = [Event(**e) for e in items.get('events', [])]
        if not self._description.enabled:
            log("History: scenario history events logging disabled", level="WARNING")

    @property
    def raw(self) -> dict[str, Any]:
        return {
            "events": [e.to_dict() for e in self.get_raw_events()]
        }

    @property
    def enabled(self) -> bool:
        return self._description.enabled

    def get_events(self) -> list[dict[str, Any]]:
        return self._description.formatter.format(self._events)

    def get_raw_events(self) -> list[Event]:
        return self._events

    def add_event(self, event: Event):
        if self.enabled:
            self._events.append(event)

    def clear(self):
        self._events.clear()

    def expire(self):
        now = time()
        non_expired = []
        for event in self._events:
            if event.created_time + self._description.event_expiration_delay > now:
                non_expired.append(event)
        self._events = non_expired

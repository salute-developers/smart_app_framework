from __future__ import annotations

from typing import Any, TYPE_CHECKING

from core.model.factory import build_factory
from core.model.registered import Registered

if TYPE_CHECKING:
    from scenarios.scenario_models.history import Event

formatters = Registered()
formatters_factory = build_factory(formatters)


class EventFormatter:

    def __init__(self, *args, **kwargs):
        pass

    def format(self, events: list[Event]) -> list[dict[str, Any]]:
        raise NotImplementedError


class HistoryEventFormatter(EventFormatter):

    def format(self, events: list[Event]) -> list[dict[str, Any]]:
        result = []
        for no, event in enumerate(events):
            formatted_event = self._format_event(event)
            formatted_event["no"] = no + 1
            result.append(formatted_event)
        return result

    def _format_event(self, event: Event) -> dict[str, Any]:
        return {
            "scenarioName": event.scenario,
            "scenarioVersion": event.scenario_version,
            "result": event.result,
            "eventType": event.type,
            "eventContent": event.content
        }

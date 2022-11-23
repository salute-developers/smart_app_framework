from functools import cached_property
from typing import Dict


class Device:
    def __init__(self, value):
        self._value = value

    @cached_property
    def value(self):
        return self._value

    @cached_property
    def platform_type(self) -> str:
        return self._value.get("platformType") or ""

    @cached_property
    def platform_version(self) -> str:
        return self._value.get("platformVersion") or ""

    @cached_property
    def surface(self) -> str:
        return self._value.get("surface") or ""

    @cached_property
    def surface_version(self) -> str:
        return self._value.get("surfaceVersion") or ""

    @cached_property
    def features(self) -> Dict:
        return self._value.get("features") or {}

    @cached_property
    def capabilities(self) -> Dict:
        return self._value.get("capabilities") or {}

    @cached_property
    def additional_info(self) -> Dict:
        return self._value.get("additionalInfo") or {}

    @cached_property
    def tenant(self) -> str:
        return self._value.get("tenant") or ""

    @cached_property
    def device_id(self) -> str:
        return self._value.get("deviceId") or ""

    @cached_property
    def ram_gb(self) -> str:
        return self._value.get("ramGb") or ""

    @cached_property
    def cpu(self) -> str:
        return self._value.get("cpu") or ""

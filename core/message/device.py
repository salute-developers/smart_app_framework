from functools import cached_property


class Device:

    def __init__(self, value):
        self._value = value

    @cached_property
    def value(self):
        return self._value

    @cached_property
    def platform_type(self):
        return self._value.get("platformType") or ""

    @cached_property
    def platform_version(self):
        return self._value.get("platformVersion") or ""

    @cached_property
    def surface(self):
        return self._value.get("surface") or ""

    @cached_property
    def surface_version(self):
        return self._value.get("surfaceVersion") or ""

    @cached_property
    def features(self):
        return self._value.get("features") or {}

    @cached_property
    def capabilities(self):
        return self._value.get("capabilities") or {}

    @cached_property
    def additional_info(self):
        return self._value.get("additionalInfo") or {}

    @cached_property
    def tenant(self):
        return self._value.get("tenant") or ""

    @cached_property
    def device_id(self):
        return self._value.get("deviceId") or ""

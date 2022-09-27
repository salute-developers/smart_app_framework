from functools import cached_property

from core.names import field


class AppInfo:

    def __init__(self, value):
        self._value = value

    @cached_property
    def project_id(self):
        return self._value.get(field.PROJECT_ID)

    @cached_property
    def system_name(self):
        return self._value.get(field.SYSTEM_NAME)

    @cached_property
    def application_id(self):
        return self._value.get(field.APPLICATION_ID)

    @cached_property
    def app_version_id(self):
        return self._value.get(field.APP_VERSION_ID)

    @cached_property
    def frontend_endpoint(self):
        return self._value.get(field.FRONTEND_ENDPOINT)

    @cached_property
    def frontend_type(self):
        return self._value.get(field.FRONTEND_TYPE)

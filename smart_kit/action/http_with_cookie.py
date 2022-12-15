import requests
from requests.cookies import RequestsCookieJar

from core.basic_models.actions.string_actions import SAVED_COOKIES
from core.logging.logger_utils import log
from smart_kit.action.http import HTTPRequestAction
from scenarios.user.user_model import User


class HTTPRequestActionWithCookie(HTTPRequestAction):
    def _set_cookies(self, user: User, cookies: RequestsCookieJar) -> None:
        whitelist = user.settings["template_settings"].get("ufs", {}).get("back_cookie_whitelist")
        if not whitelist:
            return

        cookies_to_save: dict = cookies.get_dict()
        all_cookies: dict = user.private_vars.get(SAVED_COOKIES, {})
        all_cookies.update(cookies_to_save)
        user.private_vars.set(SAVED_COOKIES, all_cookies)
        log("Cookies set", user, {
            "saved_cookies": str(all_cookies)
        }, level="DEBUG")

    def _make_response(self, request_parameters: dict, user: User) -> requests.Response:
        response = super()._make_response(request_parameters, user)
        self._set_cookies(user, response.cookies)
        return response

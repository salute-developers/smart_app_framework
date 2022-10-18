from requests.cookies import RequestsCookieJar

from core.basic_models.actions.string_actions import SAVED_COOKIE
from core.logging.logger_utils import log
from smart_kit.action.http import HTTPRequestAction
from scenarios.user.user_model import User


class HTTPRequestActionWithCookie(HTTPRequestAction):
    def _set_cookies(self, user: User, cookies: RequestsCookieJar):
        whitelist = user.settings["template_settings"]["ufs"].get("back_cookie_whitelist")
        if not whitelist:
            return

        saved = {k: v for k, v in cookies.items()}
        all_cookies: dict = user.private_vars.get(SAVED_COOKIE, {}).copy()
        all_cookies.update(saved)
        user.private_vars.set(SAVED_COOKIE, all_cookies)
        log("Cookies set", user, {
            "saved_cookies": str(saved)
        }, level="DEBUG")

    def _make_response(self, request_parameters, user):
        response = super()._make_response(request_parameters, user)
        self._set_cookies(user, response.cookies)
        return response


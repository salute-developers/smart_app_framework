from http.cookies import SimpleCookie

from core.basic_models.actions.string_actions import SAVED_COOKIES
from core.logging.logger_utils import log
from smart_kit.action.http import HTTPRequestAction
from scenarios.user.user_model import User


class HTTPRequestActionWithCookie(HTTPRequestAction):
    def _set_cookies(self, user: User, cookies: SimpleCookie) -> None:
        whitelist = user.settings["template_settings"].get("ufs", {}).get("back_cookie_whitelist")
        if not whitelist:
            return

        # cookies у aiohttp — это SimpleCookie: значения лежат в morsel.value
        cookies_to_save: dict = {name: morsel.value for name, morsel in cookies.items()}
        all_cookies: dict = user.private_vars.get(SAVED_COOKIES, {})
        all_cookies.update(cookies_to_save)
        user.private_vars.set(SAVED_COOKIES, all_cookies)
        log("Cookies set", user, {
            "saved_cookies": str(all_cookies)
        }, level="DEBUG")

    def _on_response(self, user, response):
        # cookies живут только внутри контекст-менеджера запроса — сохраняем их там
        self._set_cookies(user, response.cookies)

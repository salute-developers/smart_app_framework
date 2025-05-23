from typing import Type, Iterable, Optional
import asyncio
import signal

import scenarios.logging.logger_constants as log_const
from core.db_adapter.db_adapter import DBAdapterException
from core.db_adapter.db_adapter import db_adapter_factory
from core.logging.logger_utils import log
from core.message.from_message import SmartAppFromMessage
from core.monitoring.monitoring import monitoring
from core.monitoring.healthcheck_handler import RootResource
from core.monitoring.twisted_server import TwistedServer
from core.basic_models.parametrizers.parametrizer import BasicParametrizer
from core.message.msg_validator import MessageValidator
from scenarios.user.user_model import User
from smart_kit.start_points.postprocess import PostprocessMainLoop
from smart_kit.models.smartapp_model import SmartAppModel


class BaseMainLoop:

    def __init__(
            self, model: SmartAppModel,
            user_cls: Type[User],
            parametrizer_cls: Type[BasicParametrizer],
            postprocessor_cls: Type[PostprocessMainLoop],
            settings,
            to_msg_validators: Iterable[MessageValidator] = (),
            from_msg_validators: Iterable[MessageValidator] = (),
            *args, **kwargs
    ):
        log("%(class_name)s.__init__ started.", params={
            log_const.KEY_NAME: log_const.STARTUP_VALUE,
            "class_name": self.__class__.__name__
        })
        try:
            signal.signal(signal.SIGINT, self.stop)
            signal.signal(signal.SIGTERM, self.stop)
            self.loop = asyncio.get_event_loop()
            self.settings = settings
            self.app_name = self.settings.app_name
            self.model: SmartAppModel = model
            self.user_cls = user_cls
            self.parametrizer_cls = parametrizer_cls
            self.postprocessor = postprocessor_cls()
            self.db_adapter = self.get_db()
            self.is_work = True
            self.to_msg_validators: Iterable[MessageValidator] = to_msg_validators
            self.from_msg_validators: Iterable[MessageValidator] = from_msg_validators

            template_settings = self.settings["template_settings"]

            save_tries = template_settings.get("user_save_collisions_tries", 0)

            self.user_save_check_for_collisions = True if save_tries > 0 else False
            self.user_save_collisions_tries = max(save_tries, 1)

            self.health_check_server = self._create_health_check_server(template_settings)
            self._init_monitoring_config(template_settings)

            log("%(class_name)s.__init__ completed.", params={log_const.KEY_NAME: log_const.STARTUP_VALUE,
                                                              "class_name": self.__class__.__name__})
        except Exception:
            log("%(class_name)s.__init__ exception.", params={log_const.KEY_NAME: log_const.STARTUP_VALUE,
                                                              "class_name": self.__class__.__name__},
                level="ERROR", exc_info=True)
            raise

    def get_db(self):
        db_adapter = db_adapter_factory(self.settings["template_settings"].get("db_adapter", {}))
        if not db_adapter.IS_ASYNC:
            raise Exception(
                f"Blocking adapter {db_adapter.__class__.__name__} is not good for {self.__class__.__name__}"
            )
        self.loop.run_until_complete(db_adapter.connect())
        return db_adapter

    def _generate_answers(self, user, commands, message, **kwargs):
        raise NotImplementedError

    def _create_health_check_server(self, settings):
        health_check_server = None
        if settings["health_check"].get("enabled"):
            log("Init health_check started.", params={log_const.KEY_NAME: log_const.STARTUP_VALUE})
            health_check = settings["health_check"]
            health_check_server = TwistedServer(
                health_check["port"],
                health_check["interface"],
                RootResource,
                settings["environment"] in health_check.get("debug_envs", [])
            )
        return health_check_server

    def _init_monitoring_config(self, template_settings):
        monitoring_config = template_settings["monitoring"]
        monitoring.apply_config(monitoring_config)
        monitoring.init_metrics(app_name=self.app_name)

    async def load_user(self, db_uid: Optional[str], message: SmartAppFromMessage) -> User:
        if db_uid is None:
            log("Failed to load user data as db_uid is None. Will use empty user.", level="ERROR")
            return self.get_user(message, db_data=None, load_error=True)
        return await self._load_user(db_uid, message)

    async def _load_user(self, db_uid: str, message: SmartAppFromMessage) -> User:
        try:
            db_data = await self.db_adapter.get(db_uid)
        except (DBAdapterException, ValueError):
            log("Failed to get user data", params={log_const.KEY_NAME: log_const.FAILED_DB_INTERACTION,
                                                   log_const.REQUEST_VALUE: message.as_str}, level="ERROR")
            monitoring.counter_load_error(self.app_name)
            # to skip message when load failed
            raise
        return self.get_user(message, db_data, load_error=False)

    def get_user(self, message: SmartAppFromMessage, db_data: Optional[dict], load_error: bool) -> User:
        return self.user_cls(
            id=message.uid,
            message=message,
            db_data=db_data,
            settings=self.settings,
            descriptions=self.model.scenario_descriptions,
            parametrizer_cls=self.parametrizer_cls,
            load_error=load_error
        )

    async def save_user(self, db_uid: Optional[str], user: User, message: SmartAppFromMessage) -> bool:
        """
        :return: True if there were no any collisions when saving, False otherwise
        """
        if db_uid is None:
            log("User %(uid)s will not be saved as db_uid is None",
                user=user, level="ERROR", params={"uid": user.id})
            return True
        return await self._save_user(db_uid, user, message)

    async def _save_user(self, db_uid: str, user: User, message: SmartAppFromMessage) -> bool:
        if user.do_not_save:
            log("User %(uid)s will not be saved", user=user,
                params={"uid": user.id, log_const.KEY_NAME: "user_will_not_saved"})
            return True

        no_collisions = True
        try:
            str_data = user.raw_str
            if user.initial_db_data and self.user_save_check_for_collisions:
                no_collisions = await self.db_adapter.replace_if_equals(db_uid,
                                                                        sample=user.initial_db_data,
                                                                        data=str_data)
            else:
                await self.db_adapter.save(db_uid, str_data)
        except (DBAdapterException, ValueError):
            log("Failed to set user data", params={log_const.KEY_NAME: log_const.FAILED_DB_INTERACTION,
                                                   log_const.REQUEST_VALUE: message.as_str}, level="ERROR")
            monitoring.counter_save_error(self.app_name)
        if not no_collisions:
            monitoring.counter_save_collision(self.app_name)
        return no_collisions

    def run(self):
        raise NotImplementedError

    def stop(self, signum, frame):
        raise NotImplementedError

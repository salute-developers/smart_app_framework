import typing
from wsgiref.simple_server import make_server

import scenarios.logging.logger_constants as log_const
from core.basic_models.actions.command import Command
from core.configs.global_constants import CALLBACK_ID_HEADER
from core.logging.logger_utils import log
from core.message.from_message import SmartAppFromMessage
from core.utils.stats_timer import StatsTimer
from smart_kit.compatibility.commands import combine_commands
from smart_kit.message.smartapp_to_message import SmartAppToMessage
from smart_kit.names import message_names
from smart_kit.start_points.base_main_loop import BaseMainLoop
from smart_kit.configs import get_app_config


class BaseHttpMainLoop(BaseMainLoop):
    HEADER_START_WITH = "HTTP_SMART_APP_"
    BAD_REQUEST_COMMAND = Command(message_names.ERROR, {"code": -1, "description": "Invalid Message"})
    NO_ANSWER_COMMAND = Command(message_names.NOTHING_FOUND)

    def run(self):
        raise NotImplementedError

    def stop(self, signum, frame):
        raise NotImplementedError

    def handle_message(self, message: SmartAppFromMessage) -> typing.Tuple[int, str, SmartAppToMessage]:
        if not message.validate():
            return 400, "BAD REQUEST", SmartAppToMessage(self.BAD_REQUEST_COMMAND, message=message, request=None)

        answer, stats = self.process_message(message)
        if not answer:
            return 204, "NO CONTENT", SmartAppToMessage(self.NO_ANSWER_COMMAND, message=message, request=None)

        return 200, "OK", SmartAppToMessage(answer, message, request=None)

    def process_message(self, message: SmartAppFromMessage, *args, **kwargs):
        stats = ""
        log("INCOMING DATA: {}".format(message.masked_value),
            params={log_const.KEY_NAME: "incoming_policy_message"})
        db_uid = message.db_uid

        with StatsTimer() as load_timer:
            user = self.load_user(db_uid, message)
        stats += "Loading time: {} msecs\n".format(load_timer.msecs)
        with StatsTimer() as script_timer:
            commands = self.model.answer(message, user)
            if commands:
                answer = self._generate_answers(user, commands, message)
            else:
                answer = None

        stats += "Script time: {} msecs\n".format(script_timer.msecs)
        with StatsTimer() as save_timer:
            self.save_user(db_uid, user, message)
        stats += "Saving time: {} msecs\n".format(save_timer.msecs)
        log(stats, params={log_const.KEY_NAME: "timings"})
        return answer, stats

    def _get_headers(self, environ):
        return [(key, value) for key, value in environ.items() if key.startswith(self.HEADER_START_WITH)]

    # noinspection PyMethodMayBeStatic
    def _get_outgoing_headers(self, incoming_headers, command=None):
        headers = {"CONTENT_TYPE": "application/json"}
        headers.update(incoming_headers)

        if command:
            callback_id = command.request_data.get(CALLBACK_ID_HEADER)
            if callback_id:
                headers[CALLBACK_ID_HEADER] = callback_id

        return list(headers.items())

    def _generate_answers(self, user, commands, message, **kwargs):
        commands = combine_commands(commands, user)
        if len(commands) > 1:
            raise ValueError
        answer = commands.pop() if commands else None

        return answer


class HttpMainLoop(BaseHttpMainLoop):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._server = None

    def __call__(self, environ, start_response):
        return self.iterate(environ, start_response)

    def iterate(self, environ, start_response):
        try:
            content_length = int(environ.get('CONTENT_LENGTH', '0'))
            body = environ["wsgi.input"].read(content_length).decode()
            headers = self._get_headers(environ)
        except KeyError:
            log("Error in request data", level="ERROR")
            raise Exception("Error in request data")

        message = SmartAppFromMessage(body, headers=headers, headers_required=False,
                                      validators=get_app_config().FROM_MSG_VALIDATORS)

        status, reason, answer = self.handle_message(message)

        start_response(f"{status} {reason}", self._get_outgoing_headers(headers, answer.command))
        return [answer.value.encode()]

    def run(self):
        self._server = make_server('localhost', 8000, self.iterate)
        log(
            '''
                Application start via "python manage.py run_app" recommended only for local testing. 
                For production it is recommended to start using "gunicorn --config wsgi_config.py 'wsgi:create_app()'
            ''',
            level="WARNING")
        self._server.serve_forever()

    def stop(self, signum, frame):
        if self._server:
            self._server.server_close()
        exit(0)

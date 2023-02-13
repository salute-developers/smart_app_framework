from smart_kit.testing.local import CLInterface


class CustomLocalTesting(CLInterface):
    """Эмулятор взаимодействия навыка с внешними системами

    Формат функции-эмулятора ответа: on_<message_name>(self, message),
    где <message_name> - это тип сообщения, написанный в нижнем регистре
    Пример:
        def on_back_get_token_request(self, message):
            # BACK_GET_TOKEN_REQUEST - тип сообщения
            return json.dumps({
                "messageId": self.environment.message_id,
                "messageName": "BACK_GET_TOKEN_RESPONSE",
                "uuid": {
                    "userChannel": self.environment.user_channel,
                    "userId": self.environment.user_id,
                    "chatId": self.environment.chat_id
                },
                "payload": {
                    "token": "test",
                }
           })

    Для использования данного эмулятора присвойте переменной LOCAL_TESTING в app_config этот класс как значение.
    """
    pass

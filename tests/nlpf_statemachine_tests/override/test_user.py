"""
# Тесты на nlpf_statemachine.override.user.
"""
import json
from random import randint
from typing import Type, Optional

from pydantic import BaseModel, Field

from nlpf_statemachine.models import BaseMessage, Context, RequestMessageName
from nlpf_statemachine.override import SMUser
from tests.nlpf_statemachine_tests.utils import SMAsyncioTestCaseBase, random_string


class TestUser(SMAsyncioTestCaseBase):
    """
    # Тесты на объект User в StateMachine.
    """

    SMART_KIT_APP_CONFIG = "nlpf_statemachine.example.app_config"

    def test_success_build_init(self) -> None:
        """
        ## Тест на инициализацию объекта User с нуля.

        То есть до этого инстанса стейт-машины не существовало и объект pd_context генерируется с нуля.
        """
        message = self.mocks.smart_app_from_message()
        user = self.mocks.user(message=message)

        assert isinstance(user.context_pd, Context)
        assert isinstance(user.message_pd, BaseMessage)
        assert user.message_pd.messageName == message.message_name
        assert user.message_pd.payload.model_dump() == message.payload
        assert user.raw.get("context_pd") == Context().model_dump(exclude={"local"}, exclude_none=True)

    def test_success_build_not_init(self) -> None:
        """
        ## Тест на инициализацию объекта User с наличием данных в БД.
        """
        message = self.mocks.smart_app_from_message()
        context = Context(
            id=random_string(),
            screen=random_string(),
            event=random_string(),
            last_screen=random_string(),
            last_event=random_string(),
            last_response_message_name=random_string(),
            last_intent=random_string(),
        )
        user = self.mocks.user(message=message, db_data=json.dumps({"context_pd": context.model_dump()}))

        assert isinstance(user.context_pd, Context)
        assert isinstance(user.message_pd, BaseMessage)
        assert user.message_pd.messageName == message.message_name
        assert user.message_pd.payload.model_dump() == message.payload
        assert user.context_pd == context
        assert user.raw.get("context_pd") == context.model_dump(exclude={"local"}, exclude_none=True)

    def test_fail_on_model_search(self) -> None:
        """
        ## Тест на инициализацию объекта User с отсутствием подходящей модели для запроса.
        """
        message = self.mocks.smart_app_from_message(
            message={
                "messageName": RequestMessageName.MESSAGE_TO_SKILL,
                "messageId": randint(0, 1000000),
                "sessionId": random_string(),
                "uuid": {},
                "payload": {},
            },
        )
        user = self.mocks.user(message=message)

        assert isinstance(user.context_pd, Context)
        assert user.message_pd is None

    def test_fail_on_db_data_parse(self) -> None:
        """
        ## Тест на инициализацию объекта User с ломанными данными в БД.
        """
        message = self.mocks.smart_app_from_message()
        user = self.mocks.user(message=message, db_data="{kek")

        assert isinstance(user.context_pd, Context)
        assert isinstance(user.message_pd, BaseMessage)
        assert user.message_pd.messageName == message.message_name
        assert user.message_pd.payload.model_dump() == message.payload
        assert user.raw.get("context_pd") == Context().model_dump(exclude={"local"}, exclude_none=True)

    def test_fail_on_context_model_build(self) -> None:
        """
        ## Тест на инициализацию объекта User с неверными данными в БД относительно контекста.
        """

        class SomeField(BaseModel):
            """
            # Модель с обязательным полем.
            """

            required_field: str

        class CustomContext(Context):
            """
            # Пример переопределение Context с обязательным вложенным полем.
            """

            field: Optional[SomeField] = Field(default=None)

        class CustomUser(SMUser):
            """
            # Пример переопределение SMUser с обязательным вложенным полем в контексте.
            """

            @property
            def context_model(self) -> Type[Context]:
                """
                ## Определение модели для контекста.

                Returns:
                    Type[Context]
                """
                return CustomContext

        message = self.mocks.smart_app_from_message()
        user = self.mocks.user(message=message, user_cls=CustomUser)
        assert isinstance(user.context_pd, CustomContext)
        assert user.raw.get("context_pd") == Context().model_dump(exclude={"local"}, exclude_none=True)

        user = self.mocks.user(
            message=message,
            db_data=json.dumps(
                {
                    "context_pd": {},
                },
            ),
            user_cls=CustomUser,
        )
        assert isinstance(user.context_pd, CustomContext)
        assert user.raw.get("context_pd") == Context().model_dump(exclude={"local"}, exclude_none=True)

        user = self.mocks.user(
            message=message,
            db_data=json.dumps(
                {
                    "context_pd": {"field": {}},
                },
            ),
            user_cls=CustomUser,
        )
        assert isinstance(user.context_pd, CustomContext)
        assert user.raw.get("context_pd") == Context().model_dump(exclude={"local"}, exclude_none=True)

        data = {"field": {"required_field": random_string()}}
        user = self.mocks.user(
            message=message,
            db_data=json.dumps(
                {
                    "context_pd": data,
                },
            ),
            user_cls=CustomUser,
        )
        assert isinstance(user.context_pd, CustomContext)
        assert user.raw.get("context_pd") != Context().model_dump(exclude={"local"}, exclude_none=True)
        assert user.raw.get("context_pd") == CustomContext(**data).model_dump(exclude={"local"}, exclude_none=True)

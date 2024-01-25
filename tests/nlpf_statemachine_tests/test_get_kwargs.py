"""
# Тесты на nlpf_statemachine.utils.get_kwargs.
"""
from typing import Any
from unittest import TestCase

from nlpf_statemachine.models import (
    AppInfo,
    AssistantMessage,
    AssistantMeta,
    AssistantPayload,
    AssistantState,
    BaseMessage,
    Context,
    CurrentApp,
    ServerAction,
    ServerActionMessage,
    ServerActionPayload,
)
from nlpf_statemachine.utils.base_utils import get_kwargs
from tests.nlpf_statemachine_tests.utils import random_guid


class TestScenarioSimpleEvent(TestCase):
    """
    # Тесты на механизм извлечения параметров из функции.
    """

    def test_get_kwargs_free(self) -> None:
        """
        ## Тест на запрос запрос отсутствующих параметров.
        """

        # ==== Mocks ====
        def action() -> None:
            pass

        # ==== Run ====
        kwargs = get_kwargs(
            function=action,
            message=BaseMessage(messageName="TEST"),
            context=Context(),
            form={},
        )

        # ==== Asserts ====
        assert len(kwargs) == 0

    def test_get_kwargs_assistant_message(self) -> None:
        """
        ## Тест на запрос AssistantMessage.
        """
        # ==== Mocks ====
        state = AssistantState(screen="TestScreen")
        app_info = AppInfo(projectId=random_guid())
        payload = AssistantPayload(
            meta=AssistantMeta(
                current_app=CurrentApp(
                    state=state,
                ),
            ),
            app_info=app_info,
        )
        message = AssistantMessage(messageName="TEST", payload=payload)
        context = Context()
        form = {"form_key": "form_value"}

        def action(
                state: AssistantState,
                payload: AssistantPayload,
                form: dict,
                context: Context,
                server_action: ServerAction,
                message: AssistantMessage,
                app_info: AppInfo,
        ) -> None:
            """Тестовый экшен."""

        # ==== Run ====
        kwargs = get_kwargs(
            function=action,
            message=message,
            context=context,
            form=form,
        )

        # ==== Asserts ====
        assert len(kwargs) == 7
        assert kwargs["state"] == state
        assert kwargs["payload"] == payload
        assert kwargs["form"] == form
        assert kwargs["message"] == message
        assert kwargs["context"] == context
        assert kwargs["app_info"] == app_info
        assert kwargs["server_action"] is None

    def test_get_kwargs_server_action(self) -> None:
        """
        ## Тест на запрос ServerAction.
        """
        # ==== Mocks ====
        server_action = ServerAction(action_id="TEST_ACTION")
        payload = ServerActionPayload(
            server_action=server_action,
        )
        message = ServerActionMessage(payload=payload)
        context = Context()
        form = {"form_key": "form_value"}

        def action(
                context: Context,
                server_action: ServerAction,
                message: AssistantMessage,
                state: AssistantState,
                payload: AssistantPayload,
                form: dict,
                app_info: AppInfo,
        ) -> None:
            """Тестовый экшен."""

        # ==== Run ====
        kwargs = get_kwargs(
            function=action,
            message=message,
            context=context,
            form=form,
        )

        # ==== Asserts ====
        assert len(kwargs) == 7
        assert kwargs["state"] is None
        assert kwargs["payload"] == payload
        assert kwargs["form"] == form
        assert kwargs["message"] == message
        assert kwargs["context"] == context
        assert kwargs["server_action"] == server_action
        assert kwargs["app_info"] is None

    def test_get_kwargs_bad_params(self) -> None:
        """
        ## Тест на работу с левыми параметрами.

        Параметры должны быть со значением None.
        """

        # ==== Mocks ====
        def action(some_param: Any, other_param: Any) -> None:
            pass

        kwargs = get_kwargs(
            function=action,
            message=BaseMessage(messageName="TEST"),
            context=Context(),
            form={},
        )

        # ==== Asserts ====
        assert len(kwargs) == 2
        assert kwargs["some_param"] is None
        assert kwargs["other_param"] is None

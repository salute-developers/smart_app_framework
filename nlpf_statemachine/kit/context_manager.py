# coding: utf-8
"""
# Мозг приложения.

**Context Manager** --- это основная сущность, которая аггрегирует в себе весь каркас приложения (все сценарии)
и управляет обработкой запроса в runtime. По сути является "мозгом" всего приложения.
"""

from datetime import datetime
from typing import Any, Callable, Dict, Optional, Tuple

from core.logging.logger_utils import behaviour_log
from core.text_preprocessing.preprocessing_result import TextPreprocessingResult
from nlpf_statemachine.config import SMConfig
from nlpf_statemachine.const import GLOBAL_NODE_NAME
from nlpf_statemachine.kit.errors import ActionWithNoAnswerError, ActionWithNoValidAnswerError
from nlpf_statemachine.models import (
    AssistantMessage,
    AssistantResponsePayload,
    BaseMessage,
    Context,
    DoNothing,
    ErrorResponse,
    Event,
    IntegrationResponse,
    LocalContext,
    MessageToSkill,
    NothingFound,
    RequestData,
    Response,
)
from nlpf_statemachine.override.user import SMUser
from nlpf_statemachine.utils.base_utils import get_kwargs
from .classifier import Classifier
from .form import Form
from .screen import Scenario, Screen


class ScenarioContainer:
    """
    # Контейнер всех сценариев приложения (глобальный и экраны).
    """

    screens: Dict[str, Screen]
    """Множество экранов."""

    global_scenario: Scenario
    """Глобальный сценарий."""

    isolated_scenarios: Dict[str, Tuple[Callable, Scenario]]
    """Независимые условные сценарии для запросов с особым flow обработки."""

    def __init__(self) -> None:
        self.screens = {}
        self.global_scenario = Scenario(GLOBAL_NODE_NAME)
        self.isolated_scenarios = {}

    # ======== DESIGN TIME ========
    def add_screen(self, screen: Screen) -> None:
        """
        ## Добавление нового экрана в приложении.

        Args:
            screen (nlpf_statemachine.kit.screen.Screen): Экран

        Returns:
            None
        """
        self.screens[screen.id] = screen

    def add_scenario(self, scenario: Scenario) -> None:
        """
        ## Добавление нового сценария в приложение.

        По сути является расширением глобальноо сценария.
        Подробнее: `nlpf_statemachine.kit.scenario.Scenario.extend`.

        Args:
            scenario (nlpf_statemachine.kit.scenario.Scenario): Сценарий

        Returns:
            None
        """
        self.global_scenario.extend(scenario=scenario)

    def add_isolated_scenario(self, scenario: Scenario, condition: Callable) -> None:
        """
        ## Добавление нового изолированного сценария для запросов с особым flow обработки.

        Примеры возможных изолированных сценариев:
        * единая точка входа на запуск приложения;
        * обработка запросов item_selector.

        Args:
            scenario (nlpf_statemachine.kit.scenario.Scenario): Сценарий
            condition: Условие запуска сценария

        Returns:
            None
        """
        self.isolated_scenarios[scenario.id] = (condition, scenario)

    def add_error_action(self, action: Callable, enabled: Optional[bool] = True) -> None:
        """
        ## Добавление глобального обработчика ошибок.

        Подробнее: `nlpf_statemachine.kit.scenario.Scenario.add_error_action`.

        Args:
            action (nlpf_statemachine.kit.actions.Action or Callable): Экшен, является обработчиком ошибки
            enabled (bool, optional): Флаг для отключения данного экшена

        Returns:
            None
        """
        self.global_scenario.add_error_action(action=action, enabled=enabled)

    def add_fallback_action(self, action: Callable, enabled: Optional[bool] = True) -> None:
        """
        ## Добавление экшена на обработку глобального фоллбека.

        Подробнее: `nlpf_statemachine.kit.scenario.Scenario.add_fallback_action`.

        Args:
            action (nlpf_statemachine.kit.actions.Action or Callable): Экшен, является обработчиком фоллбека
            enabled (bool, optional): Флаг для отключения данного экшена

        Returns:
            None
        """
        self.global_scenario.add_fallback_action(action=action, enabled=enabled)

    def add_form(self, form: Form) -> None:
        """
        ## Добавление глобальной формы.

        Подробнее: `nlpf_statemachine.kit.scenario.Scenario.add_form`.

        Args:
            form (nlpf_statemachine.kit.form.Form): Форма

        Returns:
            None
        """
        self.global_scenario.add_form(form=form)

    def add_classifier(self, classifier: Classifier) -> None:
        """
        ## Добавление глобального классификатора.

        Подробнее: `nlpf_statemachine.kit.scenario.Scenario.add_classifier`.

        Args:
            classifier (nlpf_statemachine.kit.classifier.Classifier): Классификатор

        Returns:
            None
        """
        self.global_scenario.add_classifier(classifier=classifier)

    def add_action(
            self, event: str, action: Callable, base_event: Optional[str] = None, enabled: Optional[bool] = None,
    ) -> None:
        """
        ## Добавление глобального экшена к событию.

        **Best Practice:** *Лучше использовать сценарии для агрегации отдельных экшенов,
        вместо поштучного добавления их в `ContextManager`*

        Args:
            event (str): Событие, к котрому привязывается экшен
            action (nlpf_statemachine.kit.actions.Action or Callable): Экшен, который привязывается к событию
                (функция обработчик)
            base_event (str, optional): Базовое событие
            enabled (bool, optional): Флаг для отключения данного экшена

        Returns:
            None
        """
        self.global_scenario.add_action(event=event, base_event=base_event, action=action, enabled=enabled)

    def add_timeout_action(
            self, action: Callable, request_name: Optional[str] = None, base_event: Optional[str] = None,
            enabled: Optional[bool] = None,
    ) -> None:
        """
        ## Добавление экшена к таймауту на запрос.

        Подробнее: `nlpf_statemachine.kit.scenario.Scenario.add_timeout_action`.

        **Best Practice:** *Все экшены, связанные с одной интеграцией,
        лучше складывать в рамках одного самостоятельного сценария.*

        Args:
            action (nlpf_statemachine.kit.actions.Action or Callable): Экшен, который привязывается к таймауту
            request_name (str, optional): Наименования запроса, к таймауту котрого привязывается экшен
            base_event (str, optional): Базовое событие
            enabled (bool, optional): Флаг для отключения данного экшена

        Returns:
            None
        """
        self.global_scenario.add_timeout_action(
            action=action, request_name=request_name, base_event=base_event, enabled=enabled,
        )


class ContextManager(ScenarioContainer):
    """
    # ContextManager (Мозг приложения).

    Добавление основных частей сценария происходит за счёт методов родительского класса `ScenarioContainer`.
    """

    def __init__(self, run_smart_app_framework_base_kit: bool = False) -> None:
        """
        ## Инициализация ContextManager.

        Args:
            run_smart_app_framework_base_kit (bool, optional): Флаг включения стандартного SmartApp Framework Kit
                                                               default: False
        """
        super(ContextManager, self).__init__()
        self.run_smart_app_framework_base_kit = run_smart_app_framework_base_kit
        self._pre_process = None
        self._post_process = None

    def add_pre_process(self, process: Callable) -> None:
        """
        ## Добавление пре-процесса.

        Пре-процесс --- процесс, который запускается в начале каждой транзакции.

        Args:
            process (Callable): Процесс

        Returns:
            None
        """
        self._pre_process = process

    def add_post_process(self, process: Callable) -> None:
        """
        ## Добавление пост-процесса.

        Пост-процесс --- процесс, который запускается в конце каждой транзакции.

        Args:
            process (Callable): Процесс

        Returns:
            None
        """
        self._post_process = process

    @staticmethod
    def get_screen(message: AssistantMessage) -> Optional[str]:
        """
        ## Определение screen из AssistantMessage.

        **Важно:** *Можно переопределить в своём аппе.*

        Args:
            message (AssistantMessage): Тело запроса

        Returns:
            str: Наименование страницы
        """
        return message.payload.meta.current_app.state.screen

    def _get_screen_id(self, message: BaseMessage) -> Optional[str]:
        """
        ## Получить информацию о текущем screen name.

        Args:
            message (BaseMessage): Тело запроса

        Returns:
            str: Наименование страницы
        """
        if isinstance(message, AssistantMessage):
            try:
                return self.get_screen(message=message)
            except AttributeError:
                behaviour_log("Screen not defined", level="DEBUG", params={"message_id": message.messageId})

    def _get_screen(self, message: BaseMessage, context: Context) -> Optional[Screen]:
        """
        ## Получить информацию о текущей странице и передача информации в контекст.

        Args:
            message (BaseMessage): Тело запроса
            context (Context): Контекст

        Returns:
            str: Текущая страница
        """
        screen_id = self._get_screen_id(message=message)
        if screen_id:
            context.screen = screen_id
        return self.screens.get(context.screen, None)

    def _get_isolated_scenario(self, context: Context) -> Scenario:
        """
        ## Получение изолированного сценария.

        Args:
            context (Context): Контекст

        Returns:
            Scenario: Изолированный сценарий
        """
        _, scenario = self.isolated_scenarios[context.local.isolated_scenario_id]
        return scenario

    def _classify_intent(
            self, screen: Screen, message: MessageToSkill, context: Context, form: Dict,
            text_preprocessing_result: TextPreprocessingResult, user: SMUser,
    ) -> Optional[str]:
        """
        ## Определение интента.

        Args:
            screen (Screen): Экран
            message (MessageToSkill): Тело запроса
            context (Context): Контекст
            form (Dict): Форма
            text_preprocessing_result (TextPreprocessingResult): Предобработанные данные голосового запроса
            user (SMUser): Пользователь

        Returns:
            str: Интент
        """
        intent = None
        if context.local.run_isolated_scenario:
            scenario = self._get_isolated_scenario(context)
            intent = scenario.run_classifier(
                message=message, context=context, form=form, text_preprocessing_result=text_preprocessing_result,
                user=user,
            )
            if intent:
                behaviour_log(
                    f"Got intent={intent} on isolated scenario id={scenario.id}.",
                    params={"intent": intent, "scenario": scenario.id}, level="INFO", user=user,
                )
            else:
                behaviour_log(
                    "Intent is not defined on isolated scenario id={scenario.id}.",
                    params={"intent": intent, "scenario": scenario.id}, level="WARNING", user=user,
                )

        else:
            if screen:
                intent = screen.run_classifier(
                    message=message, context=context, form=form, text_preprocessing_result=text_preprocessing_result,
                    user=user,
                )

            if not intent:
                intent = self.global_scenario.run_classifier(
                    message=message, context=context, form=form, text_preprocessing_result=text_preprocessing_result,
                    user=user,
                )

                if intent:
                    behaviour_log(
                        f"Got global intent: {intent}", level="INFO",
                        params={"intent": intent, "screen": screen.id if screen else None}, user=user,
                    )
                else:
                    behaviour_log(
                        "Intent is not defined", params={"screen": screen.id if screen else None}, level="WARNING",
                        user=user,
                    )
            else:
                behaviour_log(
                    f"Got intent={intent} on screen id={screen.id if screen else None}.",
                    params={"intent": intent, "screen": screen.id if screen else None}, level="INFO", user=user,
                )

        return intent

    def _fill_form(
            self, screen: Screen, message: MessageToSkill, context: Context,
            text_preprocessing_result: TextPreprocessingResult, user: SMUser,
    ) -> Dict[str, Any]:
        """
        ## Заполнение формы.

        Args:
            screen (Screen): Экран
            message (MessageToSkill): Тело запроса
            context (Context): Контекст
            text_preprocessing_result (TextPreprocessingResult): Предобработанные данные голосового запроса
            user (SMUser): Пользователь

        Returns:
            Dict: Форма
        """
        form = self.global_scenario.fill_form(
            message=message, context=context, text_preprocessing_result=text_preprocessing_result, user=user,
        )
        if screen:
            form.update(
                screen.fill_form(
                    message=message, context=context, text_preprocessing_result=text_preprocessing_result, user=user,
                ),
            )
        return form

    def _define_event(
            self, event: Optional[str], screen: Screen, message: BaseMessage, context: Context, form: Dict,
            text_preprocessing_result: TextPreprocessingResult, user: SMUser,
    ) -> Optional[str]:
        """
        ## Определение события.

        Args:
            screen (Screen): Экран
            message (MessageToSkill): Тело запроса
            context (Context): Контекст
            form (Dict): Форма
            text_preprocessing_result (TextPreprocessingResult): Предобработанные данные голосового запроса
            user (SMUser): Пользователь

        Returns:
            str: Событие
        """
        if not event and isinstance(message, MessageToSkill):
            event = self._classify_intent(
                screen=screen, message=message, context=context, form=form,
                text_preprocessing_result=text_preprocessing_result, user=user,
            )
        context.event = event
        return event

    @staticmethod
    def _generate_local_context(user: SMUser) -> LocalContext:
        """
        ## Генерация локального контенста.

        Args:
            user (SMUser): Пользователь

        Returns:
            LocalContext: Локальный контекст
        """
        return user.local_context_model()

    # ==== Transactions ====
    @staticmethod
    def _now() -> float:
        """
        ## Текущее время.
        """
        return datetime.now().timestamp()

    @staticmethod
    def _clear_user_on_run(user: SMUser) -> None:
        """
        ## Очистка данных по транзакции у пользователя.
        """
        callback_id = user.message.callback_id
        if callback_id:
            user.behaviors._delete(callback_id=callback_id)
            user.behaviors._add_returned_callback(callback_id=callback_id)

    @staticmethod
    def _generate_callback(user: SMUser, request_data: RequestData) -> None:
        """
        ## Генерация ID для идентификации транзакции.
        """
        callback_id = user.message.generate_new_callback_id()
        user.behaviors.add(callback_id=callback_id, behavior_id=SMConfig.default_integration_behaviour_id)
        request_data.app_callback_id = callback_id

    def _set_transaction_timestamp(self, context: Context) -> None:
        """
        ## Установка времени последнего события транзакции.
        """
        context.local.last_transaction_step_timestamp = self._now()

    def _init_transaction(
            self, message: BaseMessage, user: SMUser, request_data: RequestData, context: Context,
    ) -> None:
        """
        ## Инициализация транзакции.

        Args:
            message (BaseMessage): Сообщение
            context (Context): Контекст
            user (SMUser): Пользователь
            request_data (RequestData): Данные запроса

        Returns:
            None
        """
        behaviour_log(f"Transaction started on event {context.event}.", level="INFO", user=user)
        context.local.base_event = context.event
        context.local.base_message = message
        self._generate_callback(user=user, request_data=request_data)
        self._set_transaction_timestamp(context=context)

    def _finish_transaction(
            self, response: Response, message: BaseMessage, context: Context, user: SMUser,
    ) -> Response:
        """
        ## Завершение транзакции: очистка данных по транзакции, выполнение пост-процесса.

        Args:
            response (Response): Ответ
            message (MessageToSkill): Тело запроса
            context (Context): Контекст
            user (SMUser): Пользователь

        Returns:
            Response: Ответ
        """
        context.last_screen = context.screen
        self._clear_user_on_run(user=user)
        updated_response = self._run_post_process(response=response, message=message, context=context)
        context.event = None
        context.local.base_message = None

        if updated_response is not None:
            response = updated_response

        if response is not None:
            if isinstance(response.payload, AssistantResponsePayload) and not response.payload.intent:
                response.payload.intent = context.last_intent
            response.debug_info.transaction_finished = True

        return response

    def _continue_transaction(self, user: SMUser, request_data: RequestData, context: Context) -> None:
        """
        ## Продолжение транзакции.

        Args:
            context (Context): Контекст
            user (SMUser): Пользователь
            request_data (RequestData): Данные запроса

        Returns:
            Response: Ответ
        """
        behaviour_log(
            f"Transaction continue on event {context.event} with base event {context.local.base_event}.", level="INFO",
            user=user,
        )
        self._clear_user_on_run(user=user)
        self._generate_callback(user=user, request_data=request_data)
        self._set_transaction_timestamp(context=context)

    def _transaction_exist(self, context: Context) -> bool:
        """
        ## Проверка существования активной транзакции.
        """
        return (context.local.base_event and context.local.last_transaction_step_timestamp and
                (self._now() - context.local.last_transaction_step_timestamp) < SMConfig.transaction_timeout)

    # ==== RUN action ====
    async def _run_event(
            self, event: str, screen: Screen, message: BaseMessage, context: Context, form: Dict,
    ) -> Optional[Response]:
        """
        ## Запуск обработчика любого события.

        Примеры:

        * интент;
        * Server Action;
        * ответ от интеграции;
        * ...

        Args:
            event (str): Событие
            screen (Screen): Экран
            message (BaseMessage): Сообщение
            context (Context): Контекст
            form (Dict): Форма

        Returns:
            Response
        """
        response = None
        if context.local.run_isolated_scenario:
            scenario = self._get_isolated_scenario(context)
            response = await scenario.run_event(event=event, message=message, context=context, form=form)
        else:
            if screen:
                response = await screen.run_event(event=event, message=message, context=context, form=form)
            if not response:
                response = await self.global_scenario.run_event(
                    event=event, message=message, context=context, form=form,
                )
        return response

    async def _run_timeout(self, screen: Screen, message: BaseMessage, context: Context) -> Optional[Response]:
        """
        ## Запуск обработчика на таймаут ответа от интеграций в рамках транзакций.

        Args:
            screen (Screen): Экран
            message (BaseMessage): Сообщение
            context (Context): Контекст

        Returns:
            Response
        """

        behaviour_log(
            "Run timeout.", params={"screen": screen.id if screen else None, "message_id": message.messageId},
            level="INFO",
        )

        response = None

        if context.local.run_isolated_scenario:
            scenario = self._get_isolated_scenario(context)
            response = await scenario.run_timeout_action(message=message, context=context, form={})

            if not response:
                response = await scenario.run_default_timeout_action(message=message, context=context, form={})

        if not response and screen:
            response = await screen.run_timeout_action(message=message, context=context, form={})

        if not response:
            response = await self.global_scenario.run_timeout_action(message=message, context=context, form={})

        if not response and screen:
            response = await screen.run_default_timeout_action(message=message, context=context, form={})

        if not response:
            response = await self.global_scenario.run_default_timeout_action(message=message, context=context, form={})

        return response

    async def _run_fallback(
            self, screen: Screen, message: MessageToSkill, context: Context, form: Dict,
    ) -> Optional[Response]:
        """
        ## Запуск обработчика fallback. Значит, не смогли найти подходящего обработчика на голосовой запрос.

        Args:
            screen (Screen): Экран
            message (MessageToSkill): Сообщение
            context (Context): Контекст
            form (Dict): Форма

        Returns:
            Response
        """
        response = None
        if context.local.run_isolated_scenario:
            scenario = self._get_isolated_scenario(context)
            response = await scenario.run_fallback(message=message, context=context, form={})

        if not response and screen:
            response = await screen.run_fallback(message=message, context=context, form=form)

        if not response:
            response = await self.global_scenario.run_fallback(message=message, context=context, form=form)
        return response

    async def _run_error_action(self, screen: Screen, message: BaseMessage, context: Context) -> Optional[Response]:
        """
        ## Запуск обработчика ошибки. Запускается, если ломается обработчик на текущее событие.

        Args:
            screen (Screen): Экран
            message (BaseMessage): Сообщение
            context (Context): Контекст

        Returns:
            Response
        """
        response = None
        if context.local.run_isolated_scenario:
            scenario = self._get_isolated_scenario(context)
            response = await scenario.run_error_action(message=message, context=context, form={})

        if screen:
            response = await screen.run_error_action(message=message, context=context, form={})

        if not response:
            response = await self.global_scenario.run_error_action(message=message, context=context, form={})

        if not response:
            raise Exception("None of the error actions worked.")

        return response

    # ==== Response Process ====
    def _process_response(self, response: Response, message: BaseMessage, context: Context, user: SMUser) -> Response:
        """
        ## Формирование ответа после отрабатывания экшена.

        Args:
            response (Response): Ответ
            message (BaseMessage): Сообщение
            context (Context): Контекст
            user (SMUser): Пользователь

        Returns:
            Response
        """
        response.debug_info.call_history = context.local.call_history
        response.debug_info.base_event = context.local.base_event

        if isinstance(message, AssistantMessage):
            context.last_intent = message.payload.intent

        if response.messageName in SMConfig.transaction_massage_name_finish_list:
            response = self._finish_transaction(response=response, message=message, context=context, user=user)

        elif isinstance(response, IntegrationResponse):
            response.debug_info.transaction_finished = False

            if self._transaction_exist(context=context):
                self._continue_transaction(user=user, request_data=response.request_data, context=context)
            else:
                self._init_transaction(message=message, user=user, request_data=response.request_data, context=context)
        else:
            response.debug_info.transaction_finished = True
            behaviour_log(f"Unknown response type: {type(response)}", level="WARNING", user=user)

        return response

    # ==== Run StateMachine ====
    def _run_pre_process(self, event: Optional[str], message: BaseMessage, context: Context) -> BaseMessage:
        """
        ## Запуск дополнительноых действий перед исполнения основной логики обработки запроса.

        Можно обозначить определенные действия, которые будут происходить с входящими сообщениями перед тем как будет
        начинаться основная логика обработки данного сообщения.
        Например: очистка голосового запроса или проверка поверхности.

        Args:
            event (str): Событие
            message (BaseMessage): Сообщение
            context (Context): Контекст

        Returns:
            BaseMessage
        """
        if self._pre_process:
            kwargs = get_kwargs(
                function=self._pre_process, event=event, message=message, context=context,
            )
            updated_message = self._pre_process(**kwargs)
            if isinstance(updated_message, BaseMessage):
                message = updated_message

        for key, (condition, _) in self.isolated_scenarios.items():
            kwargs = get_kwargs(
                function=condition, event=event, message=message, context=context,
            )
            if condition(**kwargs):
                behaviour_log(f"Run isolated scenario: {key}.", level="INFO", params={"message_id": message.messageId})
                context.local.isolated_scenario_id = key
                context.local.run_isolated_scenario = True
        return message

    def _run_post_process(self, response: Response, message: BaseMessage, context: Context) -> Optional[Response]:
        """
        ## Запуск дополнительноых действий после исполнения основной логики обработки запроса.

        Можно обозначить определенные действия, которые будут происходить с исходящими сообщениями после того как
        закончилась основная логика обработки данного сообщения.
        Например: добавление команды или фразы.

        Args:
            response (Response): Ответ
            message (BaseMessage): Сообщение
            context (Context): Контекст

        Returns:
            Response
        """
        if self._post_process:
            kwargs = get_kwargs(
                function=self._post_process, response=response, message=message, context=context,
            )
            return self._post_process(**kwargs)

    @staticmethod
    def _default_response(event: Optional[str] = None) -> Optional[Response]:
        """
        ## Генерация дефолтного ответа от ContextManager.

        Args:
            event (str, optional): Событие, которое пришло в context manager.

        Returns:
            NothingFound: если флаг run_smart_app_framework_base_kit = False;
            None: если флаг run_smart_app_framework_base_kit = True;
        """
        if event:
            return DoNothing()
        else:
            return NothingFound()

    @staticmethod
    def _default_error() -> Response:
        """
        ## Дефолтный обработчик ошибки.

        Срабатывает, если всё развалилось.
        """
        return ErrorResponse()

    async def _run_process(
            self, event: Optional[str], screen: Optional[Screen], message: BaseMessage, context: Context,
            text_preprocessing_result: TextPreprocessingResult, user: SMUser,
    ) -> Tuple[str, Optional[Response]]:
        """
        ## Определение и запуск пользовательского обработчика.

        Внутри выполняются пользовательские функции, которые пишут разработчики кастомного сценария.
        Они могут поломаться!

        Args:
            event (str): Событие
            screen (Screen): Экран
            message (MessageToSkill): Тело запроса
            context (Context): Контекст
            text_preprocessing_result (TextPreprocessingResult): Предобработанные данные голосового запроса
            user (SMUser): Пользователь

        Returns:
            str: Событие
            Response: Ответ
        """
        response = None
        if event == Event.LOCAL_TIMEOUT:
            context.event = event
            response = await self._run_timeout(screen=screen, message=message, context=context)
        else:
            if isinstance(message, MessageToSkill):  # or isinstance(message, RunApp):
                form = self._fill_form(
                    screen=screen, message=message, context=context,
                    text_preprocessing_result=text_preprocessing_result, user=user,
                )
            else:
                form = {}

            event = self._define_event(
                event=event, screen=screen, message=message, context=context, form=form,
                text_preprocessing_result=text_preprocessing_result, user=user,
            )

            if event:
                response = await self._run_event(
                    event=event, screen=screen, message=message, context=context, form=form,
                )
            if not response and isinstance(message, MessageToSkill):
                response = await self._run_fallback(screen=screen, message=message, context=context, form=form)
        return event, response

    async def _run(
            self, event: Optional[str], message: BaseMessage, context: Context,
            text_preprocessing_result: TextPreprocessingResult, user: SMUser,
    ) -> Response:
        """
        ## Обработка запроса.

        Args:
            event (str): Событие
            message (MessageToSkill): Тело запроса
            context (Context): Контекст
            text_preprocessing_result (TextPreprocessingResult): Предобработанные данные голосового запроса
            user (SMUser): Пользователь

        Returns:
            Response: Ответ
        """
        try:
            screen = None

            if not self._transaction_exist(context):
                context.local = self._generate_local_context(user)
                context.local.init_event = event
                if isinstance(message, AssistantMessage) and message.payload.character:
                    context.local.character_id = message.payload.character.id

                message = self._run_pre_process(event=event, message=message, context=context)

            try:
                screen = self._get_screen(message=message, context=context)
                if screen:
                    behaviour_log(f"Screen defined: {screen.id}.", user=user)
                else:
                    behaviour_log("Screen undefined.", user=user)

                _, response = await self._run_process(
                    event=event, screen=screen, message=message, context=context,
                    text_preprocessing_result=text_preprocessing_result, user=user,
                )

            except ActionWithNoAnswerError as exception:
                if context.local.run_isolated_scenario:
                    behaviour_log(
                        f"Isolated scenario returned nothing from action = {exception.action}. "
                        f"Run global StateMachine.", level="INFO", user=user,
                    )

                    context.local.run_isolated_scenario = False
                    context.local.isolated_scenario_id = None

                    if not self._transaction_exist(context):
                        self._init_transaction(message=message, user=user, request_data=RequestData(), context=context)

                    return await self._run(
                        event=context.local.init_event, message=context.local.base_message, context=context,
                        text_preprocessing_result=text_preprocessing_result, user=user,
                    )
                else:
                    behaviour_log(
                        f"ActionWithNoAnswerException: action {exception.action} returned nothing.", level="ERROR",
                        exc_info=True, user=user,
                    )
                    response = await self._run_error_action(screen=screen, message=message, context=context)

            except ActionWithNoValidAnswerError as exception:
                behaviour_log(
                    f"ActionWithNoValidAnswerException: action {exception.action} returned not valid "
                    f"response {type(exception.response)}.", level="ERROR", exc_info=True, user=user,
                )
                response = await self._run_error_action(screen=screen, message=message, context=context)

            except Exception as exception:
                behaviour_log(f"Exception in StateMachine: {exception}", level="ERROR", exc_info=True, user=user)
                response = await self._run_error_action(screen=screen, message=message, context=context)

            if isinstance(response, Response):
                response = self._process_response(response=response, message=message, context=context, user=user)
            else:
                behaviour_log("StateMachine has no response.", level="WARNING", user=user)
                if not self.run_smart_app_framework_base_kit:
                    response = self._default_response(event=event)
                    response = self._finish_transaction(response=response, message=message, context=context, user=user)

        except Exception as exception:
            behaviour_log(
                f"Exception in StateMachine (default error handler): {exception}.", level="ERROR", exc_info=True,
                user=user,
            )
            response = self._default_error()

        return response

    async def run(
            self, event: Optional[str], message: BaseMessage, context: Context,
            text_preprocessing_result: TextPreprocessingResult, user: SMUser,
    ) -> Optional[Response]:
        """
        ## Основной метод запуска обработки запроса.

        *Метод используется в runtime.*

        Args:
            event (str, optional): событие, которое произошло (опциональное поле, для MessageToSkill
                                   событие может быть определено классификацией
            message (nlpf_statemachine.models.message.protocol.assistant_message.BaseMessage): Тело запроса
            context (nlpf_statemachine.models.context.Context): Контекст
            text_preprocessing_result: NLPF TextPreprocessingResult
            user (nlpf_statemachine.override.user.SMUser): Объект NLPF User

        Returns:
            None
            Response: Наследник объекта AssistantResponse;
        """
        behaviour_log(
            f"Run ContextManager with event {event} and message of type {type(message)}.", level="INFO", user=user,
        )

        response = await self._run(
            event=event, message=message, context=context, text_preprocessing_result=text_preprocessing_result,
            user=user,
        )

        if response:
            behaviour_log("ContextManager response.", level="INFO", user=user,
                          params={"sm_response": response.model_dump()})
        else:
            behaviour_log("ContextManager response is None.", level="INFO", user=user)

        return response

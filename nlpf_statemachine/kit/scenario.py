# coding: utf-8
"""
# Сценарий.

**Сценарий** --- это основной контейнер всех обработчиков запросов в рамках приложения.

В нём собраны:

0. Экшены --- обработчики возможных событий (`nlpf_statemachine.kit.actions`);
0. Форма
    * *в design time:* множество объектов, которые умеют заполнять слоты (параметры запроса),
    * *в runtime:* множество слотов.
0. Классификаторы --- классификаторы для определения событий на сценарии.

Сценарии можно выносить в библотеки и переиспользовать в разных проектах.

Для упрощения разработки сценариев имеются 4 декоратора:

0. `nlpf_statemachine.kit.scenario.Scenario.on_event` - объявление обработчика события;
0. `nlpf_statemachine.kit.scenario.Scenario.on_timeout` - объявление обработчика таймаута в интеграциях;
0. `nlpf_statemachine.kit.scenario.Scenario.on_error` - объявление обработчика ошибки;
0. `nlpf_statemachine.kit.scenario.Scenario.on_fallback` - объявление обработчика фоллбека;

## Пример простого сценария.

```python
scenario = Scenario("ScenarioName")

@scenario.on_event(event="EVENT_1")
def action_1(message: AssistantMessage, context: Context, form: Form) -> Response:
    # Обработчик события EVENT_1.
    ...

@scenario.on_event(event="EVENT_2")
def action_2(message: AssistantMessage, context: Context, form: Form) -> Response:
    # Обработчик события EVENT_2.
    ...

@scenario.on_fallback()
def fallback_action(message: AssistantMessage, context: Context, form: Form) -> Response:
    # Обработчик фоллбека.
    ...

@scenario.on_error()
def error_action(message: BaseMessage, context: Context, form: Form) -> ErrorResponse:
    # Обработчик ошибки.
    ...

```
"""

from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional

from core.logging.logger_utils import behaviour_log
from nlpf_statemachine.const import DEFAULT_ACTION
from nlpf_statemachine.kit.actions import Action, GeneratedAction, RequirementAction
from nlpf_statemachine.kit.classifier import Classifier
from nlpf_statemachine.kit.form import Form
from nlpf_statemachine.models import BaseMessage, CallHistoryItem, Context, Event, MessageToSkill, Response
from nlpf_statemachine.override.user import SMUser


class Scenario:
    """
    # Основной класс сценарий.
    """

    id: str
    """Идентификатор текущего сценария. Для страниц должен совпадать с наименованием экрана"""

    classifiers: List[Classifier]
    """Множество классификаторов на сценарии"""

    form: Optional[Form]
    """Описание формы на сценарии (множество функция для извлечения слотов)"""

    actions: Dict[str, Dict[str, List[Action]]]
    """
    Словарь экшенов
    Структура: событие -> словарь базовых событий к экшенам
    """

    fallback_action: Optional[Action]
    """Экшен на фоллбэк (срабатывает, когда не найден обработчик на голосовой запрос)"""

    error_action: Optional[Action]
    """Экшен на ошибку (срабатывает, если вылетает ошибка в экшенах)"""

    timeout_actions: Dict[str, Dict[str, List[Action]]]
    """
    Словарь экшенов на таймаут в интеграцию
    Структура: наименование запроса -> словарь базовых событий к экшенам
    """

    default_timeout_action: Optional[Action]
    """Дефолтный экшен на таймаут (срабатывает, если не приходит ответ от интеграции"""

    def __init__(self, id: str) -> None:
        super(Scenario, self).__init__()
        self.id = id
        self.form = None
        self.classifiers = []
        self.actions = {}
        self.timeout_actions = {}
        self.fallback_action = None
        self.default_timeout_action = None
        self.error_action = None

    # ==== DesignTime Methods ====
    @staticmethod
    def _extend_actions_dict(base_actions: Dict[str, Dict[str, List[Action]]],
                             scenario_actions: Dict[str, Dict[str, List[Action]]]) -> None:
        """
        ## Добавление экшенов со стороннего сценария.
        """
        if scenario_actions:
            for event, actions_dict in scenario_actions.items():
                if event in base_actions:
                    for base_event, actions in actions_dict.items():
                        if base_event in base_actions[event]:
                            base_actions[event][base_event].extend(actions)
                        else:
                            base_actions[event][base_event] = actions
                else:
                    base_actions[event] = actions_dict

    def _generate_action(self, action: Action or Callable, enabled: Optional[bool] = None) -> Action:
        """
        ## Генерация экшена из функции.
        """
        if not isinstance(action, RequirementAction):
            if "__name__" in dir(action):
                _id = f"{self.id}.{action.__name__}"
            else:
                _id = f"{self.id}.{action.__class__.__name__}"

            # add requirements on last event?
            action = GeneratedAction(id=_id, action=action, requirements=[])

        if isinstance(enabled, bool):
            action.ENABLED = enabled

        return action

    def _add_action(self,
                    event: str,
                    container: Dict,
                    action: Action or Callable,
                    base_event: Optional[str] = None,
                    enabled: Optional[bool] = None) -> None:
        """
        ## Добавление экшена в контейнер.
        """
        action = self._generate_action(action=action, enabled=enabled)

        if event not in container:
            container[event] = {}

        base_event = base_event or DEFAULT_ACTION
        if base_event in container[event]:
            container[event][base_event].append(action)
        else:
            container[event][base_event] = [action]

    def extend(self, scenario: Scenario) -> None:
        """
        ## Расширение текщего сценария другим (перенос экшенов, классификаторов и слотов с формы).

        ## Пример использования
        Предположим, что имеется событие `event_1` и функция `action_1`, которая должна его обработать.

        ```python
        scenario_a = Scenario()
        scenario_B = Scenario()
        scenario_a.add_action(event=event_1, action=action_1)
        # В сценарии A теперь на событие event_1 будет вызван action_1.

        scenario_b.extend(scenario_A)
        # В сценарии B теперь на событие event_1 будет также action_1.
        ```

        Args:
            scenario (Scenario): другой сценарий

        Returns:
            None
        """
        behaviour_log(f"Extend scenario {self.id} with {scenario.id}", level="INFO")
        self._extend_actions_dict(self.actions, scenario.actions)
        self._extend_actions_dict(self.timeout_actions, scenario.timeout_actions)

        if scenario.form:
            if self.form:
                self.form.extend(scenario.form)
            else:
                self.form = scenario.form
        if scenario.classifiers:
            self.classifiers.extend(scenario.classifiers)

        if scenario.fallback_action:
            self.default_timeout_action = scenario.fallback_action
        if scenario.default_timeout_action:
            self.default_timeout_action = scenario.default_timeout_action
        if scenario.error_action:
            self.default_timeout_action = scenario.error_action

    def add_action(self,
                   event: str,
                   action: Action or Callable,
                   base_event: Optional[str] = None,
                   enabled: Optional[bool] = True) -> None:
        """
        ## Добавление экшена к событию.

        ## Пример использования
        ```python
        def action(message: BaseMessage, context: Context, form: Dict) -> Response:
            ...
        ...
        scenario.add_action(event="EVENT", action=action)
        ```

        Аналогично можно использовать декоратор `nlpf_statemachine.kit.scenario.Scenario.on_event`:
        ```python
        @scenario.on_event(event="EVENT)
        def action(message: BaseMessage, context: Context, form: Dict) -> Response:
            ...
        ```

        Args:
            event (str): Событие, к котрому привязывается экшен
            action (nlpf_statemachine.kit.actions.Action or Callable): Экшен, который привязывается к событию
                (функция обработчик)
            base_event (str, optional): Базовое событие
            enabled (bool, optional): Флаг для отключения данного экшена

        Returns:
            None
        """
        self._add_action(
            event=event,
            action=action,
            base_event=base_event,
            enabled=enabled,
            container=self.actions,
        )

    def add_action_on_multiple(
            self, events: List[str], action: Action or Callable, base_event: Optional[str] = None,
            enabled: Optional[bool] = True,
    ) -> None:
        """
        # Добавление экшена к множеству событий.

        # Пример использования
        ```python
        def add_action_on_multiple(message: BaseMessage, context: Context, form: Dict) -> Response:
            ...
        ...
        scenario.add_action_on_multiple(events=["EVENT"], action=action)
        ```

        Args:
            events (List[str]): Список событий, к которым привязывается экшен
            action (nlpf_statemachine.kit.actions.Action or Callable): Экшен, который привязывается к событию
                (функция обработчик)
            base_event (str, optional): Базовое событие
            enabled (bool, optional): Флаг для отключения данного экшена

        Returns:
            None
        """
        for event in events:
            self._add_action(
                event=event,
                action=action,
                base_event=base_event,
                enabled=enabled,
                container=self.actions,
            )

    def _add_default_timeout_action(self,
                                    action: Action or Callable,
                                    enabled: Optional[bool] = None) -> None:
        """
        ## Установка дефолтного экшена на таймаут по любому запросу.

        Args:
            action (nlpf_statemachine.kit.actions.Action or Callable): Экшен, который объявляется дефолтным таймаутом
            enabled (bool, optional): Флаг для отключения данного экшена

        Returns:
            None
        """
        self.default_timeout_action = self._generate_action(action=action, enabled=enabled)

    def add_timeout_action(self,
                           action: Action or Callable,
                           request_name: Optional[str] = None,
                           base_event: Optional[str] = None,
                           enabled: Optional[bool] = None) -> None:
        """
        ## Добавление экшена к таймауту на запрос.

        * Если отсутствует request_name, то данный таймаут становится дефолтным для всех интеграций в сценарии.
        * Если отсутствует base_event, то данный таймаут становится дефолтным для данного типа запроса в сценарии.
        * Если enabled True, то данный экшен активен, иначе он не будет вызываемым в runtime.

        ## Пример использования
        ```python
        def timeout_action(message: BaseMessage, context: Context, form: Dict) -> Response:
            ...
        ...
        scenario.add_timeout_action(action=timeout_action, request_name="REQUEST_NAME")
        ```

        Аналогично можно использовать декоратор `nlpf_statemachine.kit.scenario.Scenario.on_timeout`:
        ```python
        @scenario.on_timeout(request_name="REQUEST_NAME")
        def timeout_action(message: BaseMessage, context: Context, form: Dict) -> Response:
            ...
        ```

        Args:
            action (nlpf_statemachine.kit.actions.Action or Callable): Экшен, который привязывается к таймауту
            request_name (str, optional): Наименования запроса, к таймауту котрого привязывается экшен
            base_event (str, optional): Базовое событие
            enabled (bool, optional): Флаг для отключения данного экшена

        Returns:
            None
        """
        if request_name:
            self._add_action(
                event=request_name,
                action=action,
                base_event=base_event,
                enabled=enabled,
                container=self.timeout_actions,
            )
        else:
            self._add_default_timeout_action(action=action, enabled=enabled)

    def add_error_action(self, action: Action or Callable, enabled: Optional[bool] = True) -> None:
        """
        # Добавление экшена на обработку ошибки.

        ## Пример использования
        ```python
        def error_action(message: BaseMessage, context: Context, form: Dict) -> Response:
            ...
        ...
        scenario.add_error_action(action=error_action)
        ```

        Аналогично можно использовать декоратор `nlpf_statemachine.kit.scenario.Scenario.on_error`:
        ```python
        @scenario.on_error()
        def error_action(message: BaseMessage, context: Context, form: Dict) -> Response:
            ...
        ```

        Args:
            action (nlpf_statemachine.kit.actions.Action or Callable): Экшен, является обработчиком ошибки
            enabled (bool, optional): Флаг для отключения данного экшена

        Returns:
            None
        """
        self.error_action = self._generate_action(action=action, enabled=enabled)

    def add_fallback_action(self, action: Action or Callable, enabled: Optional[bool] = True) -> None:
        """
        # Добавление экшена на обработку фоллбека.

        ## Пример использования
        ```python
        def fallback_action(message: BaseMessage, context: Context, form: Dict) -> Response:
            ...
        ...
        scenario.add_fallback_action(action=fallback_action)
        ```

        Аналогично можно использовать декоратор `nlpf_statemachine.kit.scenario.Scenario.on_fallback`:
        ```python
        @scenario.on_fallback()
        def fallback_action(message: BaseMessage, context: Context, form: Dict) -> Response:
            ...
        ```

        Args:
            action (nlpf_statemachine.kit.actions.Action or Callable): Экшен, является обработчиком фоллбека
            enabled (bool, optional): Флаг для отключения данного экшена

        Returns:
            None
        """
        self.fallback_action = self._generate_action(action=action, enabled=enabled)

    def add_form(self, form: Form) -> None:
        """
        ## Добавление формы на сценарий.

        ## Пример использования
        ```python
        form = Form()
        scenario.add_form(form=form)
        ```

        Args:
            form (nlpf_statemachine.kit.form.Form): Форма

        Returns:
            None
        """
        if self.form:
            behaviour_log(f"Form multiple redefinition in scenario {self.id}.", level="WARNING")
        self.form = form

    def add_classifier(self, classifier: Classifier) -> None:
        """
        ## Добавление классификатора на сценарий.

        ## Пример использования
        ```python
        scenario.add_classifier(classifier=IntersectionClassifier(filename="static/path/"))
        ```

        Args:
            classifier (nlpf_statemachine.kit.classifier.Classifier): классификатор

        Returns:
            None
        """
        self.classifiers.append(classifier)

    # ==== Декораторы ====

    def on_event(self, event: str = None, base_event: Optional[str] = None,
                 enabled: Optional[bool] = True) -> Callable[[Callable[[...], Response]], Callable[[...], Response]]:
        """
        ## Декоратор на добавление обработчика события в сценарии.

        * Если отсутствует base_event, то данный экшен становится дефолтным для данного типа запроса в сценарии.
        * Если enabled True, то данный экшен активен, иначе он не будет вызываемым в runtime.

        ## Пример использования:
        ```python
        @scenario.on_event(event="EVENT)
        def action(message: BaseMessage, context: Context, form: Dict) -> Response:
            ...
        ```

        Args:
            event (str): Обрабатываемое событие
            base_event (str): Базовое событие
            enabled (bool): Флаг для отключения данного экшена

        Returns:
            Декоратор
        """

        def decorator(function: Callable[[...], Response]) -> Callable[[...], Response]:
            """Функция декоратор."""
            self.add_action(event=event, base_event=base_event, action=function, enabled=enabled)
            return function

        return decorator

    def on_multiple_events(self, events: [], base_event: Optional[str] = None, enabled: Optional[bool] = True) -> \
            Callable[[Callable[[...], Response]], Callable[[...], Response]]:
        """
        ## Декоратор на добавление обработчика для различных текущих событий и одинакового базового.

        Например: Обработка нескольких server_action у которых первый шаг поход в единую интеграцию за данными.

        Args:
            events (list): Список возможных событий
            base_event (str): Базовое событие
            enabled (bool): Флаг для отключения данного экшена

        Returns:
            Декоратор
        """

        def decorator(function: Callable[[...], Response]) -> Callable[[...], Response]:
            """Функция декоратор."""
            for event in events:
                self.add_action(event=event, base_event=base_event, action=function, enabled=enabled)
            return function

        return decorator

    def on_multiple_base_events(self, event: str, base_events: [], enabled: Optional[bool] = True) -> \
            Callable[[Callable[[...], Response]], Callable[[...], Response]]:
        """
        # Декоратор на добавления несколько обработчиков базовых событий в сценарии.

        Например: Ответ пользователю после похода в интеграцию, к которому могут приводить различные события.

        Args:
            event (str): Обрабатываемое событие
            base_events (List): Наименование базовых событий
            enabled (bool): Флаг для отключения данного экшена

        Returns:
            Декоратор
        """

        def decorator(function: Callable[[...], Response]) -> Callable[[...], Response]:
            """Функция декоратор."""
            for base_event in base_events:
                self.add_action(event=event, base_event=base_event, action=function, enabled=enabled)
            return function

        return decorator

    def on_timeout(self, request_name: Optional[str] = None, base_event: Optional[str] = None,
                   enabled: Optional[bool] = True) -> Callable[[Callable[[...], Response]], Callable[[...], Response]]:
        """
        ## Декоратор на добавление обработчика таймаута в сценарии.

        * Если отсутствует request_name, то данный таймаут становится дефолтным для всех интеграций в сценарии.
        * Если присутствует request_name, но отсутствует base_event,
          то данный таймаут становится дефолтным для данного типа запроса в сценария.
        * Если присутствуют request_name и base_event, то данный обработчик срабатывает только
          в случае указанного наименования запроса и базового события.
        * Если enabled True, то данный экшен активен, иначе он не будет вызываемым в runtime.

        ## Пример использования:
        ```python
        @scenario.on_timeout(request_name="REQUEST_NAME", base_event="EVENT")
        def action(message: BaseMessage, context: Context, form: Dict) -> Response:
            ...
        ```

        Args:
            request_name (str): Наименование запроса, таймаут на который обрабатывается
            base_event (str): Базовое событие
            enabled (bool): Флаг для отключения данного экшена

        Returns:
            Декоратор
        """

        def decorator(function: Callable[[...], Response]) -> Callable[[...], Response]:
            """Функция декоратор."""
            self.add_timeout_action(action=function, base_event=base_event, request_name=request_name, enabled=enabled)
            return function

        return decorator

    def on_error(self,
                 enabled: Optional[bool] = True) -> Callable[[Callable[[...], Response]], Callable[[...], Response]]:
        """
        ## Декоратор на добавление обработчика ошибки в сценарии.

        * Если enabled True, то данный экшен активен, иначе он не будет вызываемым в runtime.

        ## Пример использования:
        ```python
        @scenario.on_error()
        def error_action(message: BaseMessage, context: Context, form: Dict) -> Response:
            ...
        ```

        Args:
            enabled (bool): Флаг для отключения данного экшена

        Returns:
            Декоратор
        """

        def decorator(function: Callable[[...], Response]) -> Callable[[...], Response]:
            """Функция декоратор."""
            self.add_error_action(action=function, enabled=enabled)
            return function

        return decorator

    def on_fallback(self,
                    enabled: Optional[bool] = True) -> Callable[[Callable[[...], Response]], Callable[[...], Response]]:
        """
        ## Декоратор на добавление фоллбека в сценарий.

        Обработчик nlpf_statemachine.models.message.message.MessageToSkill не найден.

        * Если enabled True, то данный экшен активен, иначе он не будет вызываемым в runtime.

        ## Пример использования:
        ```python
        @scenario.on_fallback()
        def fallback_action(message: BaseMessage, context: Context, form: Dict) -> Response:
            ...
        ```

        Args:
            enabled (bool): Флаг для отключения данного экшена

        Returns:
            Декоратор
        """

        def decorator(function: Callable[[...], Response]) -> Callable[[...], Response]:
            """Функция декоратор."""
            self.add_fallback_action(action=function, enabled=enabled)
            return function

        return decorator

    # ==== Runtime Methods ====
    def fill_form(self, message: MessageToSkill, context: Context,
                  text_preprocessing_result: Any, user: SMUser) -> Dict:
        """
        ## Заполнение формы на текущем сценарии.

        *Метод используется в runtime.*

        Args:
            message (nlpf_statemachine.models.message.message.MessageToSkill): Тело запроса
                (голосовой запрос от пользователя)
            context (nlpf_statemachine.models.context.Context): Контекст
            text_preprocessing_result: Объект NLPF TextPreprocessingResult
            user (nlpf_statemachine.override.user.SMUser): Объект NLPF User

        Returns:
            Dict: словарь, с заполненными слотами.
        """
        if self.form:
            return self.form.fill(message, context, text_preprocessing_result, user)
        return {}

    def _update_call_history(self, event: str, action: Action, context: Context) -> None:
        """
        ## Обновление call_history для дебага.

        Args:
            event (str): Обрабатываемое событие
            action (nlpf_statemachine.kit.actions.Action): Обработчик события
            context (nlpf_statemachine.models.context.Context): Контекст

        Returns:
            None
        """
        context.local.call_history.append(
            CallHistoryItem(
                event=event,
                action=action.id,
                scenario=self.id,
            ),
        )

    async def _run_action(self, event: str, action: Action, message: BaseMessage,
                          context: Context, form: Dict) -> Optional[Response]:
        """
        ## Запуск экшена.

        Args:
            event (str): Обрабатываемое событие
            action (nlpf_statemachine.kit.actions.Action): Обработчик события
            message (nlpf_statemachine.models.message.protocol.assistant_message.BaseMessage): Тело запроса
            context (nlpf_statemachine.models.context.Context): Контекст
            form (Dict[str, Any]): Форма

        Returns:
            Response: ответ от экшена. (объект наследник Response)
        """
        if action.check(message=message, context=context, form=form):
            self._update_call_history(event=event, action=action, context=context)
            response = await action(message=message, context=context, form=form)
            context.last_event = event
            context.last_response_message_name = response.messageName
            return response

    async def run_event(self, event: str, message: BaseMessage, context: Context, form: Dict) -> Optional[Response]:
        """
        ## Запуск обработчика события на сценарии (поиск экшена).

        Поиск экшена происходит по следующему правилу:

        1. Поиск обработчика текущего базового события для данного события;
        2. Поиск дефолтного обработчика для данного события.

        Иначе возвращается None: необходимый action не найден.

        *Метод используется в runtime.*

        Args:
            event (str): Обрабатываемое событие
            message (nlpf_statemachine.models.message.protocol.assistant_message.BaseMessage): Тело запроса
            context (nlpf_statemachine.models.context.Context): Контекст
            form (Dict[str, Any]): Форма

        Returns:
            Response: ответ от экшена. (объект наследник Response)
        """
        if event not in self.actions:
            return None

        if context.local.base_event in self.actions[event]:
            for action in self.actions[event][context.local.base_event]:
                response = await self._run_action(event=event, message=message, action=action, context=context,
                                                  form=form)
                if response:
                    return response

        if DEFAULT_ACTION in self.actions[event]:
            for action in self.actions[event][DEFAULT_ACTION]:
                response = await self._run_action(event=event, message=message, action=action, context=context,
                                                  form=form)
                if response:
                    return response

    async def run_error_action(self, message: BaseMessage, context: Context, form: Dict) -> Optional[Response]:
        """
        ## Запуск обработчика ошибки на сценарии (если он определён).

        *Метод используется в runtime.*

        Args:
            message (nlpf_statemachine.models.message.protocol.assistant_message.BaseMessage): Тело запроса
            context (nlpf_statemachine.models.context.Context): Контекст
            form (Dict[str, Any]): Форма

        Returns:
            Response: ответ от error-экшена. (объект наследник Response)
            None: нет подходящего error-экшена

        """
        if self.error_action:
            return await self._run_action(
                event=Event.ERROR, message=message, action=self.error_action, context=context, form=form,
            )

    async def run_timeout_action(self, message: BaseMessage, context: Context, form: Dict) -> Optional[Response]:
        """
        ## Запуск обработчика таймаута на сценарии.

        Таймауты происходят в транзакциях, если интеграция не ответила.
        (поиск обработчика для текущего запроса)

        Поиск экшена происходит по следующему правилу:

        1. Поиск обработчика текущего базового события для данного наименования запроса;
        2. Поиск дефолтного обработчика для данного наименования запроса.

        *Метод используется в runtime.*

        Args:
            message (nlpf_statemachine.models.message.protocol.assistant_message.BaseMessage): Тело запроса
            context (nlpf_statemachine.models.context.Context): Контекст
            form (Dict[str, Any]): Форма

        Returns:
            Response: ответ от таймаут-экшена (объект наследник Response)
            None: нет подходящего таймаут-экшена
        """
        request_name = context.last_response_message_name
        if request_name in self.timeout_actions:
            if context.local.base_event in self.timeout_actions[request_name]:
                for action in self.timeout_actions[request_name][context.local.base_event]:
                    response = await self._run_action(
                        event=Event.LOCAL_TIMEOUT, message=message, action=action, context=context, form=form,
                    )
                    if response:
                        return response

        if request_name in self.timeout_actions:
            if DEFAULT_ACTION in self.timeout_actions[request_name]:
                for action in self.timeout_actions[request_name][DEFAULT_ACTION]:
                    response = await self._run_action(
                        event=Event.LOCAL_TIMEOUT, message=message, action=action, context=context, form=form,
                    )
                    if response:
                        return response

    async def run_default_timeout_action(
            self, message: BaseMessage, context: Context, form: Dict,
    ) -> Optional[Response]:
        """
        ## Запуск дефолтного обработчика таймаута на сценарии.

        Таймауты происходят в транзакциях, если интеграция не ответила.
        Дефолтный запускается в случае, если не нашлось обработчика таймаута для конкретного запроса.

        *Метод используется в runtime.*

        Args:
            message (nlpf_statemachine.models.message.protocol.assistant_message.BaseMessage): Тело запроса
            context (nlpf_statemachine.models.context.Context): Контекст
            form (Dict[str, Any]): Форма

        Returns:
            Response: ответ от таймаут-экшена (объект наследник Response)
            None: Дефолтный таймаут-экшен отсутствует
        """
        if self.default_timeout_action:
            return await self._run_action(
                event=Event.LOCAL_TIMEOUT, message=message,
                action=self.default_timeout_action, context=context, form=form,
            )

    async def run_fallback(self, message: MessageToSkill, context: Context, form: Dict) -> Optional[Response]:
        """
        ## Запуск обработчика фоллбека на сценарии.

        Фоллбек - это случай, когда не удалось найти обработчик для текущего запроса.
        Фоллбек должен выполняться только для голосовых запросов
        (nlpf_statemachine.models.message.message.MessageToSkill).

        *Метод используется в runtime.*

        Args:
            message (nlpf_statemachine.models.message.message.MessageToSkill): Тело запроса
            context (nlpf_statemachine.models.context.Context): Контекст
            form (Dict[str, Any]): Форма

        Returns:
            Response: ответ от фоллбек-экшена. (объект наследник Response)
            None: Дефолтный фоллбек-экшен отсутствует
        """
        if self.fallback_action:
            return await self._run_action(
                event=Event.FALLBACK, message=message, action=self.fallback_action, context=context, form=form,
            )

    def run_classifier(self, message: MessageToSkill, context: Context, form: Dict,
                       text_preprocessing_result: Any, user: SMUser) -> Optional[str]:
        """
        ## Поиск события на сценарии.

        На сценарии имеется множество классификаторов, поиск происходит последовательным запуском,
        пока интент не будет определён.

        *Метод используется в runtime.*

        Args:
            message (nlpf_statemachine.models.message.message.MessageToSkill): Тело запроса
            context (nlpf_statemachine.models.context.Context): Контекст
            form (Dict[str, Any]): Форма
            text_preprocessing_result: Объект NLPF TextPreprocessingResult
            user (nlpf_statemachine.override.user.SMUser): Объект NLPF User

        Returns:
            str: найденное событие
            None: ни одному из классификаторов не удалось установить событие

        """
        for classifier in self.classifiers:
            intent = classifier.run(message=message, context=context, form=form)
            if not intent:
                intent = classifier.run_legacy(
                    message=message, context=context, form=form,
                    text_preprocessing_result=text_preprocessing_result, user=user,
                )
            if intent:
                return intent

# -*- coding: utf-8 -*-
"""
# Экшен.

--- обработчик конкертного запроса.

## Экшен-функция.
Любой экшен можно описать в виде простой функции, которая возвращает объект наследник
`nlpf_statemachine.models.Response`.
У&nbsp;функции-экшена могут быть следующие параметры:

1. **message** --- запрос, который пришёл в сервис. Объект наследник `nlpf_statemachine.models.BaseMessage`;
2. **context** --- контекст запроса (данные, которые сохраняются между запросами)
   Объект наследник `nlpf_statemachine.models.Context`;
3. **form** ---  множество слотов, извлечённых из запросов. Словарь.;
3. **payload** ---  Коллекция, в которой передается дополнительная информация. Поле `message.payload`.
   Словарь или любая pydantic модель в зависимости от типа запроса;
3. **app_info** ---  Информация о смартапе. Объект наследник `nlpf_statemachine.models.AppInfo`.;
3. **state** ---  Состояние фронтенда. Поле `message.payload.meta.current_app.state`.
   Объект наследник `nlpf_statemachine.models.AssistantState`.;
3. **server_action** ---  Описание команды для бэкенда смартапа. Поле `message.payload.server_action`.
   Объект наследник `nlpf_statemachine.models.ServerAction`.;

Параметры являются опциональными. Если функция их ожидает, то они будут переданы в случае вызова.
Но&nbsp;их&nbsp;отсутствие к ошибке не приведёт. Параметры могут объявляться в любом порядке.

Экшен всегда должен возвращать ответ --- объект наследник pydantic-модели `nlpf_statemachine.models.Response`.

Подробнее о том, как добавлять экшен-функции можно посмотреть в разделе `nlpf_statemachine.kit.scenario`.


## Для тех, кто не любит декораторы :)

Экшены можно так же задавать явно в виде класса наследника `Action`.

"""

from typing import Any, Callable, Dict, List, Optional

from core.logging.logger_utils import behaviour_log
from nlpf_statemachine.kit.errors import ActionDisabledError, ActionWithNoAnswerError, ActionWithNoValidAnswerError
from nlpf_statemachine.models import BaseMessage, Context, Response
from nlpf_statemachine.utils.base_utils import get_kwargs


class Requirement:
    """
    # Условие на срабатывания экшена.

    Callable-объект, возвращающий **true/false**.

    Для создания своих условий рекомендовано наследоваться и определять метод run.
    """

    def __init__(self, id: str, requirement: Optional[Callable] = None) -> None:
        self.id = id
        if requirement:
            self.run = requirement

    def __call__(self, message: BaseMessage, context: Context, form: Dict[str, Any]) -> bool:
        """
        ## Вызов requirement.

        *Вызывается метод `run`.*

        Args:
            message (nlpf_statemachine.models.message.protocol.assistant_message.BaseMessage): Тело запроса.
            context (nlpf_statemachine.models.context.Context): Контекст.
            form (Dict[str, Any]): Форма

        Returns:
            bool
        """
        return self.run(message=message, context=context, form=form)

    def run(self, message: BaseMessage, context: Context, form: Dict[str, Any]) -> bool:
        """
        ## Основной метод для определения доступности экшена.

        **Рекомендация:** *переопределять.*

        Args:
            message (nlpf_statemachine.models.message.protocol.assistant_message.BaseMessage): Тело запроса.
            context (nlpf_statemachine.models.context.Context): Контекст.
            form (Dict[str, Any]): Форма

        Returns:
            bool
        """
        raise NotImplementedError


class Action:
    """
    # Базовый класс экшена.
    """

    ENABLED: bool = True
    id: Optional[str]

    def __init__(self, id: str) -> None:
        self.id = id

    async def __call__(self, message: BaseMessage, context: Context, form: Dict[str, Any]) -> Response:
        """
        ## Вызов экшена.

        *Вызывается метод `run`.*

        Args:
            message (nlpf_statemachine.models.message.protocol.assistant_message.BaseMessage): Тело запроса.
            context (nlpf_statemachine.models.context.Context): Контекст.
            form (Dict[str, Any]): Форма

        Returns:
            Response
        """
        if self.check(message=message, context=context, form=form):
            behaviour_log(f"Run action: {self.id}", params={"action": self.id, "message_id": message.messageId})
            response = await self.run(message=message, context=context, form=form)
            if not response:
                raise ActionWithNoAnswerError(action=self.id)
            if not isinstance(response, Response):
                raise ActionWithNoValidAnswerError(action=self.id, response=response)
            return response
        raise ActionDisabledError(action=self.id)

    async def run(self, message: BaseMessage, context: Context, form: Dict[str, Any]) -> Response:
        """
        ## Основной метод для вызова экшена.

        **Рекомендация:** *переопределять.*

        Args:
            message (nlpf_statemachine.models.message.protocol.assistant_message.BaseMessage): Тело запроса.
            context (nlpf_statemachine.models.context.Context): Контекст.
            form (Dict[str, Any]): Форма

        Returns:
            Response
        """
        raise NotImplementedError

    def check(self, message: BaseMessage, context: Context, form: Dict[str, Any]) -> bool:
        """
        ## Проверка доступности экшена.

        **Рекомендация:** *не переопределять в своих экшенах. Используйте для этого `RequirementAction`*
        *или `MultipleRequirementsAction`*.

        Args:
            message (nlpf_statemachine.models.message.protocol.assistant_message.BaseMessage): Тело запроса.
            context (nlpf_statemachine.models.context.Context): Контекст.
            form (Dict[str, Any]): Форма

        Returns:
            bool
        """
        return self.ENABLED


class RequirementAction(Action):
    """
    # Экшен с условием на запуск.
    """

    async def run(self, message: BaseMessage, context: Context, form: Dict[str, Any]) -> Response:
        """
        ## Основной метод для вызова экшена.

        **Рекомендация:** *переопределять.*

        Args:
            message (nlpf_statemachine.models.message.protocol.assistant_message.BaseMessage): Тело запроса.
            context (nlpf_statemachine.models.context.Context): Контекст.
            form (Dict[str, Any]): Форма

        Returns:
            Response
        """
        raise NotImplementedError

    def requirement(self, message: BaseMessage, context: Context, form: Dict[str, Any]) -> bool:
        """
        ## Основной метод для определения доступности экшена.

        **Рекомендация:** *переопределять.*

        Args:
            message (nlpf_statemachine.models.message.protocol.assistant_message.BaseMessage): Тело запроса.
            context (nlpf_statemachine.models.context.Context): Контекст.
            form (Dict[str, Any]): Форма.

        Returns:
            bool
        """
        raise NotImplementedError

    def check(self, message: BaseMessage, context: Context, form: Dict[str, Any]) -> bool:
        """
        ## Проверка доступности экшена.

        **Рекомендация:** *не переопределять в своих экшенах. Используйте для этого `RequirementAction.requirement`*
        *или `MultipleRequirementsAction`*.

        Args:
            message (nlpf_statemachine.models.message.protocol.assistant_message.BaseMessage): Тело запроса.
            context (nlpf_statemachine.models.context.Context): Контекст.
            form (Dict[str, Any]): Форма.

        Returns:
            bool
        """
        return self.ENABLED and self.requirement(message=message, context=context, form=form)


class MultipleRequirementsAction(RequirementAction):
    """
    # Экшен с множеством условий на запуск.
    """

    id: Optional[str]

    def __init__(self, id: str, requirements: Optional[List[Callable]] = None) -> None:
        super(MultipleRequirementsAction, self).__init__(id=id)
        self._requirements = []
        if requirements:
            self.add_requirements(requirements)

    async def run(self, message: BaseMessage, context: Context, form: Dict[str, Any]) -> Response:
        """
        ## Основной метод для вызова экшена.

        **Рекомендация:** *переопределять.*

        Args:
            message (nlpf_statemachine.models.message.protocol.assistant_message.BaseMessage): Тело запроса.
            context (nlpf_statemachine.models.context.Context): Контекст.
            form (Dict[str, Any]): Форма

        Returns:
            Response
        """
        raise NotImplementedError

    def requirement(self, message: BaseMessage, context: Context, form: Dict[str, Any]) -> bool:
        """
        ## Основной метод для определения доступности экшена.

        **Рекомендация:** *не переопределять. Добавляйте в __init__ через `add_requirement` или `add_requirements`.*

        Args:
            message (nlpf_statemachine.models.message.protocol.assistant_message.BaseMessage): Тело запроса.
            context (nlpf_statemachine.models.context.Context): Контекст.
            form (Dict[str, Any]): Форма.

        Returns:
            bool
        """
        for requirement in self._requirements:
            if not requirement(message=message, context=context, form=form):
                return False
        return True

    def add_requirement(self, requirement: Callable) -> None:
        """
        ## Добаление requirement.

        Args:
            requirement (Callable): Условие на доступность экшена.

        Returns:
            None
        """
        self._requirements.append(requirement)

    def add_requirements(self, requirements: List[Callable]) -> None:
        """
        ## Добаление множества requirements.

        Args:
            requirements (List[Callable]): Условия на доступность экшена.

        Returns:
            None
        """
        for requirement in requirements:
            self.add_requirement(requirement)


class GeneratedAction(MultipleRequirementsAction):
    """
    # Экшен, сгенерированный из декоратора.
    """

    def __init__(self, id: str, action: Callable, requirements: Optional[List[Callable]] = None) -> None:
        super(GeneratedAction, self).__init__(id=id, requirements=requirements)
        self._run = action

    async def run(self, message: BaseMessage, context: Context, form: Dict[str, Any]) -> Response:
        """
        ## Основной метод для вызова экшена.

        Args:
            message (nlpf_statemachine.models.message.protocol.assistant_message.BaseMessage): Тело запроса.
            context (nlpf_statemachine.models.context.Context): Контекст.
            form (Dict[str, Any]): Форма

        Returns:
            Response
        """
        kwargs = get_kwargs(function=self._run, message=message, context=context, form=form)
        return self._run(**kwargs)

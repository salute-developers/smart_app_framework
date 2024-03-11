"""# Переопределение объекта NLPF User."""
import json
from datetime import datetime
from typing import Any, Dict, List, Optional, Type

from pydantic import ValidationError

from core.descriptions.descriptions import Descriptions
from core.logging.logger_utils import behaviour_log
from core.message.from_message import SmartAppFromMessage
from nlpf_statemachine.const import DEFAULT
from nlpf_statemachine.models import (
    BaseMessage,
    Context,
    Event,
    LocalContext,
    LocalTimeout,
    MessageToSkill,
    RequestMessageName,
    ServerActionMessage,
)
from nlpf_statemachine.utils.base_utils import get_field_class
from scenarios.user.parametrizer import Parametrizer
from scenarios.user.user_model import User
from smart_kit.configs.settings import Settings


class SMUser(User):
    """
    # Переопределение объекта NLPF User.

    Добавлено:
    * В User хранится контекст;
    * В User можно переопределить модели для контекста и своего типа запроса.
    """

    def __init__(
            self, id: str, message: SmartAppFromMessage, db_data: str, settings: Settings, descriptions: Descriptions,
            parametrizer_cls: Type[Parametrizer], load_error: bool = False,
    ) -> None:
        super(SMUser, self).__init__(
            id=id, message=message, db_data=db_data, settings=settings, descriptions=descriptions,
            parametrizer_cls=parametrizer_cls, load_error=load_error,
        )
        self.message_pd = self.build_message(message.as_dict)

        try:
            user_values = json.loads(db_data) if db_data else None
        except ValueError:
            user_values = None

        if user_values:
            context = user_values.get("context_pd")

            self.local_contexts = user_values.get("local_contexts", {})
            if isinstance(self.local_contexts, dict):
                transaction_local_context = self.local_contexts.pop(str(self.message_pd.messageId), None)
            else:
                transaction_local_context = None

            self.context_pd = self.build_context(dictionary=context, current_local_context=transaction_local_context)

        else:
            self.context_pd = self.context_model()
            self.local_contexts = {}

    @property
    def message_models(self) -> Dict[str, List[Type[BaseMessage]]]:
        """
        # Определение моделей запросов.

        **Данный метод можно (и нужно!) переопределять в своём приложении для переопределения моделей запросов.**

        Структура:

        > Имя запроса: список допустимых объектов.

        *Объекты строятся последовательно!*
        Если объект построился (прошла валидация всех полей) --- успех.
        Иначе строится следующий объект.


        Returns:
            Dict[str, List[Type[BaseMessage]]]

        """
        return {
            Event.LOCAL_TIMEOUT: [LocalTimeout],
            RequestMessageName.MESSAGE_TO_SKILL: [MessageToSkill],
            RequestMessageName.SERVER_ACTION: [ServerActionMessage],
            RequestMessageName.RUN_APP: [ServerActionMessage, MessageToSkill],
            DEFAULT: [BaseMessage],
        }

    @property
    def context_model(self) -> Type[Context]:
        """
        # Определение модели для контекста.

        **Данный метод можно (и нужно!) переопределять в своём приложении для переопределения моделей запросов.**

        Returns:
            Type[Context]
        """
        return Context

    @property
    def local_context_model(self) -> Type:
        """
        ## Определение модели для контекста.

        **Данный метод можно (и нужно!) переопределять в своём приложении для переопределения моделей запросов.**

        Returns:
            Type[LocalContext]
        """
        context_class = self.context_model
        context_local_class = get_field_class(base_obj=context_class, field="local")
        return context_local_class

    @property
    def raw(self) -> Dict[str, Any]:
        """
        # Словарь, который описывает User.

        Он же сохраняется в игнайт.

        Добавлены общий контекст (context_pd) пользователя и локальные контексты транзакций (local_contexts).

        Returns:
            Dict[str, Any]
        """
        result = super(SMUser, self).raw
        result["context_pd"] = self.context_pd.model_dump(exclude={"local"}, exclude_none=True)

        if self.context_pd.local.base_message:
            self.local_contexts[self.message_pd.messageId] = self.context_pd.local.model_dump(exclude_none=True)

        result["local_contexts"] = self.local_contexts
        return result

    def build_local_context(self, dictionary: Dict[str, Any]) -> LocalContext:
        """
        # Построение pydantic-модели локального контекста из словаря.

        Args:
            dictionary (Dict[str, Any]): Словарь, по которому строится локальный контекст;

        Returns:
            LocalContext: Построенный объект локального контекста.
        """
        try:
            if dictionary:
                local_context = self.local_context_model(**dictionary)

                base_message = dictionary.get("base_message")
                if base_message:
                    base_message_model = self.build_message(base_message)
                    local_context.base_message = base_message_model
                return local_context

        except ValidationError:
            behaviour_log(f"Local_context {self.local_context_model} build failed.", level="ERROR", exc_info=True)

        return self.local_context_model()

    def build_context(self, dictionary: Dict[str, Any], current_local_context: Dict[str, Any]) -> Context:
        """
        # Построение pydantic-модели контекста из словаря.

        *Важно:* **У контекста не должно быть обязательных полей!!!**
        Args:
            dictionary (Dict[str, Any]): Словарь, по которому строится контекст;
            current_local_context (Dict[str, Any]): Локальный контекст для текущей транзакции;

        Returns:
            Context: Построенный объект контекста.
        """
        try:
            if dictionary:
                context = self.context_model(**dictionary)

                if current_local_context:
                    context.local = self.build_local_context(current_local_context)
                return context
        except ValidationError:
            behaviour_log(f"Context {self.context_model} build failed.", level="ERROR", exc_info=True)
        return self.context_model()

    def build_message(self, dictionary: Dict[str, Any]) -> Optional[BaseMessage]:
        """
        # Построение pydantic-модели запроса из словаря.

        Args:
            dictionary (Dict[str, Any]): Словарь, пришедший на вход;

        Returns:
            BaseMessage: запрос в виде pydantic-модели.
            None: не нашлось подходящего объекта.
        """
        message_name = dictionary.get("messageName", None)
        if message_name and message_name in self.message_models:
            models = self.message_models[message_name]
        else:
            models = self.message_models[DEFAULT]

        for model in models:
            try:
                message = model(**dictionary)
                behaviour_log(f"Build message {message_name} with type: {model}.", level="INFO")
                return message
            except ValidationError:
                behaviour_log(f"Model {model} build failed for message name {message_name}.", level="WARNING")
                continue

    def local_context_expiration(self) -> None:
        """
        # Очистка локального контекста.
        """
        expired_local_contexts = []
        for mid, local_context in self.local_contexts.items():
            if local_context.get("last_transaction_step_timestamp") < datetime.now().timestamp() - 60:
                expired_local_contexts.append(mid)
        for expired_local_context in expired_local_contexts:
            self.local_contexts.pop(str(expired_local_context), None)

    def expire(self) -> None:
        """
        # Дополнение метода очистки устаревших пользовательских данных.
        """
        super().expire()
        self.local_context_expiration()

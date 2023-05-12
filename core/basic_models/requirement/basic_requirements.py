import logging
import hashlib
from datetime import datetime, timezone
from functools import cached_property
from random import random
from typing import List, Optional, Dict, Any

from croniter import croniter

import core.logging.logger_constants as log_const
from core.basic_models.classifiers.basic_classifiers import Classifier, ExternalClassifier
from core.basic_models.operators.operators import Operator
from core.logging.logger_utils import log, log_classifier_result
from core.model.base_user import BaseUser
from core.model.factory import build_factory, list_factory, factory
from core.model.registered import Registered
from core.text_preprocessing.base import BaseTextPreprocessingResult
from core.text_preprocessing.preprocessing_result import TextPreprocessingResult
from core.unified_template.unified_template import UnifiedTemplate
from core.utils.stats_timer import StatsTimer
from scenarios.scenario_models.field.field_filler_description import IntersectionFieldFiller
from scenarios.user.user_model import User

requirements = Registered()

requirement_factory = build_factory(requirements)


class Requirement:
    """Класс для проверки заданного условия

    Параметры:
        items["cache_result"]   Использовать ли закешированный результат в рамках обработки сообщения и совпадения items

    Атрибуты:
        cache_result    то же, что и items["cache_result"]

    Примечания:
        Кэширование допустимо только в случае, если функция выдаёт один и тот же результат в рамках времени кэширования,
        в нашем случае - в рамках обработки одного сообщения. Таким образом, если на результат requirement влияют
        переменные, которые могут поменяться в ходе обработке сообщения, например, user.counters, то кэширование не
        подойдёт для рассматриваемого requirement.
    """
    cache_result = False

    def __init__(self, items: Dict[str, Any], id: Optional[str] = None) -> None:
        items = items or {}
        self._descr = items.get("_description")
        self.items = items
        self.version = items.get("version", -1)
        self.id = id
        self.is_logging_debug_mode = logging.getLogger(globals().get("__name__")).isEnabledFor(
            logging.getLevelName("DEBUG")
        )
        if "cache_result" in items:
            self.cache_result = items["cache_result"]

    def _log_params(self):
        return {
            log_const.KEY_NAME: log_const.REQUIREMENT_CHECK_VALUE,
            "requirement": self.__class__.__name__
        }

    def _check(self, text_preprocessing_result: BaseTextPreprocessingResult, user: BaseUser,
               params: Dict[str, Any] = None) -> bool:
        return True

    def _on_check_error_result(self, text_preprocessing_result: BaseTextPreprocessingResult, user: BaseUser) -> bool:
        # return True or False if it's acceptable in custom requirement
        raise

    def check(self, text_preprocessing_result: BaseTextPreprocessingResult, user: BaseUser,
              params: Dict[str, Any] = None) -> bool:
        if self.cache_result:
            cached_results = user.message_vars.get("cached_req_results")
            if not cached_results:
                cached_results = dict()
                user.message_vars.set("cached_req_results", cached_results)

            if self.hash_for_cache in cached_results:
                result = cached_results[self.hash_for_cache]
            else:
                try:
                    result = self._check(text_preprocessing_result, user, params)
                    cached_results[self.hash_for_cache] = result
                except Exception:
                    return self.on_check_error(text_preprocessing_result, user)
        else:
            try:
                result = self._check(text_preprocessing_result, user, params)
            except Exception:
                return self.on_check_error(text_preprocessing_result, user)
        if self.is_logging_debug_mode:
            log_params = self._log_params()
            log_params[log_const.KEY_NAME] = log_const.REQUIREMENT_TRACE_VALUE
            log_params["result"] = result
            log_params["raw_items"] = str(self.items)
            log_params["params"] = params
            if self._descr:
                log_params["descr"] = self._descr
            log(f"TRACING %(requirement)s with id {self.id}: Result is %(result)s.", user, log_params, level="DEBUG")
        return result

    def on_check_error(self, text_preprocessing_result: BaseTextPreprocessingResult, user: BaseUser):
        result = self._on_check_error_result(text_preprocessing_result, user)
        log_params = self._log_params()
        log_params["masked_message"] = str(user.message.masked_value)
        log_params["result"] = result
        log("exc_handler: Requirement FAILED to check. Return %(result)s. MESSAGE: %(masked_message)s.",
            user, log_params,
            level="ERROR", exc_info=True)
        return result

    @cached_property
    def hash_for_cache(self):
        return hashlib.md5(f"{self.__class__.__name__}{self.items}".encode()).hexdigest()


class CompositeRequirement(Requirement):
    requirements: List[Requirement]

    def __init__(self, items: Dict[str, Any], id: Optional[str] = None) -> None:
        super().__init__(items, id)
        self._requirements = items["requirements"]
        self.requirements = self.build_requirements()

    @list_factory(Requirement)
    def build_requirements(self):
        return self._requirements


class AndRequirement(CompositeRequirement):

    def _check(self, text_preprocessing_result: BaseTextPreprocessingResult, user: BaseUser,
               params: Dict[str, Any] = None) -> bool:
        return all(
            requirement.check(text_preprocessing_result=text_preprocessing_result, user=user, params=params)
            for requirement in self.requirements
        )


class OrRequirement(CompositeRequirement):

    def _check(self, text_preprocessing_result: BaseTextPreprocessingResult, user: BaseUser,
               params: Dict[str, Any] = None) -> bool:
        return any(
            requirement.check(text_preprocessing_result=text_preprocessing_result, user=user, params=params)
            for requirement in self.requirements
        )


class NotRequirement(Requirement):
    requirement: Requirement

    def __init__(self, items: Dict[str, Any], id: Optional[str] = None) -> None:
        super().__init__(items, id)
        self._requirement = items["requirement"]
        self.requirement = self.build_requirement()

    @factory(Requirement)
    def build_requirement(self):
        return self._requirement

    def _check(self, text_preprocessing_result: BaseTextPreprocessingResult, user: BaseUser,
               params: Dict[str, Any] = None) -> bool:
        return not self.requirement.check(text_preprocessing_result=text_preprocessing_result, user=user,
                                          params=params)


class ComparisonRequirement(Requirement):
    operator: Operator

    def __init__(self, items: Dict[str, Any], id: Optional[str] = None) -> None:
        super().__init__(items, id)
        self._operator = items["operator"]
        self.operator = self.build_operator()

    @factory(Operator)
    def build_operator(self):
        return self._operator


class RandomRequirement(Requirement):
    percent: int

    def __init__(self, items: Dict[str, Any], id: Optional[str] = None) -> None:
        super().__init__(items, id)
        self.percent = items["percent"]

    def _check(self, text_preprocessing_result: BaseTextPreprocessingResult, user: BaseUser,
               params: Dict[str, Any] = None) -> bool:
        result = random() * 100
        return result < self.percent


class TopicRequirement(Requirement):
    topics: List[str]

    def __init__(self, items: Dict[str, Any], id: Optional[str] = None) -> None:
        super().__init__(items, id)
        self.topics = items["topics"]

    def _check(self, text_preprocessing_result: BaseTextPreprocessingResult, user: BaseUser,
               params: Dict[str, Any] = None) -> bool:
        return user.message.topic_key in self.topics


class TemplateRequirement(Requirement):
    def __init__(self, items: Dict[str, Any], id: Optional[str] = None) -> None:
        super().__init__(items, id)
        self._template = UnifiedTemplate(items["template"])

    def _check(self, text_preprocessing_result: BaseTextPreprocessingResult, user: BaseUser,
               params: Dict[str, Any] = None) -> bool:
        params = params or {}
        collected = user.parametrizer.collect(text_preprocessing_result)
        params.update(collected)
        render_result = self._template.render(params)
        if render_result == "True":
            return True
        if render_result == "False":
            return False
        raise TypeError(f'Template result should be "True" or "False", got: '
                        f'{render_result} for template {self.items["template"]}')


class RollingRequirement(Requirement):
    percent: int

    def __init__(self, items: Dict[str, Any], id: Optional[str] = None) -> None:
        super().__init__(items, id)
        self.percent = items["percent"]

    def _check(self, text_preprocessing_result: BaseTextPreprocessingResult, user: BaseUser,
               params: Dict[str, Any] = None) -> bool:
        id = user.id
        s = id.encode('utf-8')
        hash = int(hashlib.sha256(s).hexdigest(), 16)
        res = hash % 100
        return res < self.percent


class TimeRequirement(ComparisonRequirement):
    def __init__(self, items: Dict[str, Any], id: Optional[str] = None) -> None:
        super().__init__(items, id)

    def _check(
            self,
            text_preprocessing_result: BaseTextPreprocessingResult,
            user: BaseUser,
            params: Dict[str, Any] = None
    ) -> bool:
        message_time_dict = user.message.payload['meta']['time']
        message_timestamp_sec = message_time_dict['timestamp'] // 1000
        message_time = datetime.fromtimestamp(message_timestamp_sec, tz=timezone.utc).time()
        return self.operator.compare(message_time)

    @factory(Operator)
    def build_operator(self):
        operator = dict(self._operator)
        amount_time = datetime.strptime(operator["amount"], '%H:%M:%S').time()
        operator["amount"] = amount_time
        return operator


class DateTimeRequirement(Requirement):
    match_cron: str

    def __init__(self, items: Dict[str, Any], id: Optional[str] = None) -> None:
        super().__init__(items, id)
        self.match_cron = items['match_cron']

    def _check(
            self,
            text_preprocessing_result: BaseTextPreprocessingResult,
            user: BaseUser,
            params: Dict[str, Any] = None
    ) -> bool:
        message_time_dict = user.message.payload['meta']['time']
        message_timestamp_sec = message_time_dict['timestamp'] // 1000
        message_datetime = datetime.fromtimestamp(message_timestamp_sec)
        return croniter.match(self.match_cron, message_datetime)


class IntersectionRequirement(Requirement):
    phrases: Optional[List]

    def __init__(self, items: Dict[str, Any], id: Optional[str] = None) -> None:
        super().__init__(items, id)
        self.filler = IntersectionFieldFiller(
            {
                'cases': {
                    True: items.get('phrases', []),
                },
                'default': False,
            },
            id,
        )

    def _check(
            self,
            text_preprocessing_result: TextPreprocessingResult,
            user: User,
            params: Dict[str, Any] = None
    ) -> bool:
        result = bool(self.filler.extract(text_preprocessing_result, user, params))
        return result


class ClassifierRequirement(Requirement):
    """Условие, которое зависит от результата классификации.
    Возвращает True, если результат классификации запроса относится к одной из указанных категорий, прошедших порог,
    но не равной классу other.
    """

    def __init__(self, items: Dict[str, Any], id: Optional[str] = None) -> None:
        super().__init__(items=items, id=id)
        self._classifier = items["classifier"]

    @cached_property
    def classifier(self) -> Classifier:
        return ExternalClassifier(self._classifier)

    def _check(self, text_preprocessing_result: BaseTextPreprocessingResult, user: BaseUser,
               params: Dict[str, Any] = None) -> bool:
        check_res = True
        classifier = self.classifier
        with StatsTimer() as timer:
            classification_res = classifier.find_best_answer(
                text_preprocessing_result, scenario_classifiers=user.descriptions["external_classifiers"])

        log_classifier_result(classification_res, user, classifier, timer)

        if not classification_res or classification_res[0][classifier.class_other]:
            check_res = False

        return check_res


class FormFieldValueRequirement(Requirement):
    """Условие возвращает True, если в форме form_name в поле field_name значение совпадает с переданным value,
    иначе - False. Данное условие предназначено только для плоских форм.
    """

    def __init__(self, items: Dict[str, Any], id: Optional[str] = None) -> None:
        super().__init__(items, id)
        self.form_name = items["form_name"]
        self.field_name = items["field_name"]
        self.value = items["value"]

    def _check(self, text_preprocessing_result: BaseTextPreprocessingResult, user: User,
               params: Dict[str, Any] = None) -> bool:
        return user.forms[self.form_name].fields[self.field_name].value == self.value


class EnvironmentRequirement(Requirement):
    """Условие возвращает True, если сценарий исполняется на стенде из числа values, иначе - False.
    Так, например, можно ограничить сценарий для исполнения только на тестовых средах.
    Возможные значения в values: ift, uat, pt, prod (это ИФТ, ПСИ, НТ, ПРОМ).
    """

    def __init__(self, items: Dict[str, Any], id: Optional[str] = None) -> None:
        super().__init__(items, id)
        self.values = items.get("values", [])
        # Из конфига получаем среду исполнения
        from smart_kit.configs import get_app_config
        app_config = get_app_config()
        self.environment = app_config.ENVIRONMENT
        # Если среда исполнения задана, то проверям, что среда в списке возможных значений для сценария, иначе - False
        self.check_result = self.environment in self.values if self.environment else False

    def _check(self, text_preprocessing_result: BaseTextPreprocessingResult, user: BaseUser,
               params: Dict[str, Any] = None) -> bool:
        return self.check_result


class CharacterIdRequirement(Requirement):
    """Условие возвращает True, если идентификатор выбранного персонажа входит
    в список значений, иначе - False.
    """

    def __init__(self, items: Dict[str, Any], id: Optional[str] = None) -> None:
        super().__init__(items=items, id=id)
        self.values = items["values"]

    def _check(self, text_preprocessing_result: BaseTextPreprocessingResult, user: User,
               params: Dict[str, Any] = None) -> bool:
        return user.message.payload["character"]["id"] in self.values


class FeatureToggleRequirement(Requirement):
    """Условие возвращает True, если проверка указанного тогла по названию возвращает True, иначе - False.
    Тоглы задаются в template_config.yml, с помощью значений True и False их можно включить или выключить.
    """

    def __init__(self, items: Dict[str, Any], id: Optional[str] = None) -> None:
        super().__init__(items=items, id=id)
        self.toggle_name = items["toggle_name"]

    def _check(self, text_preprocessing_result: BaseTextPreprocessingResult, user: User,
               params: Dict[str, Any] = None) -> bool:
        return user.settings["template_settings"].get(self.toggle_name, False)

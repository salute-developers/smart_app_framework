"""
# Пример работы с формами и IntersectionClassifier.

* *Форма* --- это множество извлечённых из фразы пользователя сущностей.
* *Филлер* --- это объект, который отвечает за извлечение слотов из фразы.

Филлеры могут быть 2х типов:
1. Самописные филлеры, наследники класса `Filler`.
2. Классические SmartApp Framework `FieldFillerDescription`.
   Полный список можно посмотреть в модуле `scenarios.scenario_models.field.field_filler_description`;

В данном примере создадим форму с двумя слотами:
1. Извлекаем число из фразы пользователя (самописный филлер);
2. `example.sc.fillers.approve_filler.ApproveFiller` - пример использования NLPF `FieldFillerDescription`.

В качестве классификатора используется IntersectionClassifier
--- классификатор на основе вхождения ключевых фраз в строку.
Анализ происходит с использованием раздела `tokenized_element_list` в запросе.

**Замечание:** Примеры сделаны максимально простыми.
Исключительно с целью показать механизм работы с `IntersectionClassifier`, создания филлеров и формы.
"""
from typing import Dict

from nlpf_statemachine.example.app.sc.commands import generate_item
from nlpf_statemachine.example.app.sc.fillers.approve_filler import CustomApproveFiller, no_words, yes_words
from nlpf_statemachine.example.app.sc.models.commands import FormCommand
from nlpf_statemachine.kit import Form, IntersectionClassifier, Scenario
from nlpf_statemachine.models import AnswerToUser, AssistantResponsePayload
from scenarios.scenario_models.field.field_filler_description import ApproveFiller
from smart_kit.configs import get_app_config

# 1. Создаём форму и добавляем на неё соответствующие слоты.
my_form = Form()
my_form.add_field(
    name="nlpf_approve",
    filler=ApproveFiller(
        items={
            "yes_words": yes_words,
            "no_words": no_words,
        },
    ),
)
my_form.add_field(
    name="custom_approve",
    filler=CustomApproveFiller(),
)

# 2. Определяем простой классификатор для нашего сценария.
app_config = get_app_config()
classifier = IntersectionClassifier(
    filename=f"{app_config.STATIC_PATH}/intents/global.yaml",
)

# 3. Определяем сценарий, используюший данную форму.
scenario = Scenario("FORM_FILLING_SCENARIO")
scenario.add_form(form=my_form)
scenario.add_classifier(classifier=classifier)


# 4. Определяем экшен, который будет обрабатывать значения в слотах.
@scenario.on_event(event="APPROVE")
@scenario.on_event(event="REJECT")
def form_filling_approve_action(form: Dict) -> AnswerToUser:
    """
    # Пример работы с формой и IntersectionClassifier.

    **Событие:** `FORM_FILLING_EVENT`. (определяется классификатором на основе вхождения ключевых фраз)

    Args:
        form (Dict): форма (словарь).

    Returns:
        AnswerToUser: Ответ с командой FormCommand.
    """
    return AnswerToUser(
        payload=AssistantResponsePayload(
            items=[
                generate_item(smart_app_data=FormCommand(
                    nlpf_approve=form.get("nlpf_approve"),
                    custom_approve=form.get("custom_approve"),
                )),
            ],
        ),
    )

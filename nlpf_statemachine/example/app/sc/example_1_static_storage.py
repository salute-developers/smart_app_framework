"""
# Пример работы с StaticStorage и простым классификатором.

Классификатор на основе original_text + tokenized_element_list.
"""
from nlpf_statemachine.example.app.sc.classifiers.original_text_classifier import Events, OriginalTextClassifier
from nlpf_statemachine.example.app.sc.commands import custom_command
from nlpf_statemachine.kit import Scenario, StaticStorageManager
from nlpf_statemachine.models import AnswerToUser, Context, FileFormat
from smart_kit.configs import get_app_config

# 1. Создадим StaticStorageManager для работы со статикой.
app_config = get_app_config()
example_storage = StaticStorageManager(
    filename=f"{app_config.STATIC_PATH}/scenario/storage_example.yaml",
    file_format=FileFormat.YAML,
)

# 2. Инициализируем сценарий
scenario = Scenario("StaticStorageExample")

# 3. Добавляем классификаторы.
#    Нас интересует события Events.STATIC_STORAGE_EVENT_X.
scenario.add_classifier(classifier=OriginalTextClassifier())


# 4. Добавим обработчики событии Events.STATIC_STORAGE_EVENT_X.
#    Ответ сгенерируем из example_storage.
@scenario.on_event(event=Events.STATIC_STORAGE_EVENT_1)
def example_storage_action_1() -> AnswerToUser:
    """
    ## Кейс 1.

    **Фиксированный ответ на верхнем уровне.**

    Returns:
        AnswerToUser: Ответ из StaticStorage.
    """
    return example_storage.answer_to_user(code="EXAMPLE_1")


@scenario.on_event(event=Events.STATIC_STORAGE_EVENT_2)
def example_storage_action_2(context: Context) -> AnswerToUser:
    """
    ## Кейс 2.

    ** Ответ выбирается для соответствующего ассистента (с наличием полей на верхних уровнях) **
    ** с вариативностью ответов. **

    Returns:
        AnswerToUser: Ответ из StaticStorage.
    """
    return example_storage.answer_to_user(code="EXAMPLE_2", context=context)


@scenario.on_event(event=Events.STATIC_STORAGE_EVENT_3)
def example_storage_action_3(context: Context) -> AnswerToUser:
    """
    ## Кейс 3.

    ** Ответ выбирается независимо от асситента (с наличием полей на верхних уровнях) **
    ** и вариативностью ответов. **

    Returns:
        AnswerToUser: Ответ из StaticStorage.
    """
    return example_storage.answer_to_user(code="EXAMPLE_3", context=context)


@scenario.on_event(event=Events.STATIC_STORAGE_EVENT_4)
def example_storage_action_4(context: Context) -> AnswerToUser:
    """
    ## Кейс 4.

    ** Добавление команды в голосовой ответ из статики. **

    Returns:
        AnswerToUser: Ответ из StaticStorage и команда.
    """
    response = example_storage.answer_to_user(code="EXAMPLE_4", context=context)
    response.payload.items.append(custom_command("value1", 3))
    return response

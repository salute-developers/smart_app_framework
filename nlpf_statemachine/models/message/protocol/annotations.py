"""
# Общие характеристики сообщения пользователя.
"""

from typing import List

from pydantic import BaseModel, Field


class AnnotationsDetails(BaseModel):
    """
    # Описание модели AnnotationsDetails.
    """

    classes: List[str] = Field(default_factory=list)
    """
    Список вариаций аннотаций.
    """
    probas: List[int] = Field(default_factory=list)
    """
    Список вероятностей соответствующих аннотаций.
    """


class Annotations(BaseModel):
    """
    # Описание модели Annotations.

    Общие характеристики сообщения пользователя.
    """

    censor_data: AnnotationsDetails
    """
    Информация о прохождении цензуры.

    `AnnotationsDetails.classes` --- список подцензурных категорий, обнаруженных в тексте или реплике пользователя.

    Содержит следующие значения:

    * politicians — наличие политиков из списка
    * obscene — наличие нецензурной лексики
    * model_response — вероятность негатива

    `AnnotationsDetails.probas` --- коэффициенты подцензурных категорий.
    Сопоставляются по индексам, в соотвествии со списком категорий `AnnotationsDetails.classes`.

    Для категорий politicians и obscene могут принимать только значения 0 и 1.
    """
    text_sentiment: AnnotationsDetails
    """
    Эмоциональная окраска текста пользователя.

    `AnnotationsDetails.classes` --- список характеристик эмоциональной окраски текста пользователя.

    Содержит следующие значения:

    * negative
    * positive
    * neutral

    `AnnotationsDetails.probas` --- коэффициенты той или иной эмоциональной характеристики
    текста пользователя в диапазоне от 0 до 1.
    Коэффициенты сопоставляются по индексам с характеристиками, представленными в поле text_sentiment.classes.
    """
    asr_sentiment: AnnotationsDetails
    """
    Эмоциональная окраска голоса пользователя.

    `AnnotationsDetails.classes` --- список характеристик эмоциональной окраски голоса пользователя.

    Содержит следующие значения:

    * negative
    * positive
    * neutral

    `AnnotationsDetails.probas` --- коэффициенты той или иной эмоциональной характеристики реплики пользователя
    в диапазоне от 0 до 1.
    Коэффициенты сопоставляются по индексам с характеристиками, представленными в поле asr_sentiment .classes.
    """

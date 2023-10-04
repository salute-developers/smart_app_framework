from typing import Optional, Union, Match, Dict, List
import re

MASK = "***"
DEFAULT_MASKING_FIELDS = {
    "token": 0, "access_token": 0, "refresh_token": 0, "epkId": 0, "ucp_id": 0, "profileId": 0, "searchResult": 0,
}
CARD_MASKING_FIELDS = ["message", "debug_info", "normalizedMessage", "normalized_text",
                       "incoming_text", "annotations", "inner_entities",
                       "preprocess_result", "original_message", "original_tokenized_elements", "lemma",
                       "original_text", "asr_original_message", "asr_normalized_message",
                       "human_normalized_text", "human_normalized_text_with_anaphora",
                       "unified_normalized_text", "ner_prediction"]


card_regular = re.compile(r"(?:(\d{18})|(\d{16})|(?:\d{4} ){3}(\d{4})(\s?\d{2})?)")


class Counter(object):
    # Класс счетчик для маскировки структуры, items - кол-во простых элементов, collections - коллекций
    # max_depth - максимальная глубина
    def __init__(self):
        self.items = 0
        self.collections = 0
        self.max_depth = 0


def luhn_checksum(card_number: str) -> bool:
    digits = [int(d) for d in card_number]
    odd_digits = digits[-1::-2]
    even_digits = digits[-2::-2]
    checksum = sum(odd_digits) + sum(map(lambda x: (x * 2) % 10 + (x * 2) // 10, even_digits))
    return checksum % 10 == 0


def card_sub_func(x: Match[str]) -> str:
    d_regular = re.compile(r"\d")

    g0 = x.group(0)
    is_last_not_digit = int(g0 and not g0[-1].isdigit())
    last_char = g0[-1]

    mask = d_regular.sub("*", x.group(0))[:-(4 + is_last_not_digit)]
    digs = (x.group(0) or '').replace(' ', '')[-4:]
    return mask + digs + (last_char * is_last_not_digit)


def masking(data: Union[Dict, List], masking_fields: Optional[Union[Dict, List]] = None,
            depth_level: int = 2, mask_available_depth: int = -1,
            white_list: Optional[List[str]] = None) -> Union[Dict, List]:
    """
    :param data: коллекция для маскирования приватных данных
    :param masking_fields: поля для обязательной маскировки независимо от уровня
    :param white_list: поля, которые не должны маскироваться
    :param depth_level: глубина сохранения структуры маскируемого поля
    :param mask_available_depth: глубина глубокой маскировки полей без сохранения структуры (см ниже)
    """

    if isinstance(masking_fields, list):
        masking_fields = {key: depth_level for key in masking_fields}

    if masking_fields is None:
        masking_fields = DEFAULT_MASKING_FIELDS

    return _masking(data, masking_fields, depth_level, mask_available_depth,
                    masking_on=False, card_masking_on=False, white_list=white_list)


def _masking(data: Union[Dict, List], masking_fields: Union[Dict, List],
             depth_level: int = 2, mask_available_depth: int = -1, masking_on: bool = False,
             card_masking_on: bool = False, white_list: Optional[List[str]] = None) -> Union[Dict, List]:

    # тут в зависимости от листа или словаря создаем итератор
    if isinstance(data, dict):
        key_gen = data.items()
        masked_data = dict()
    else:
        key_gen = enumerate(data)
        masked_data = [None for _ in range(len(data))]

    for key, _ in key_gen:
        value_is_collection = isinstance(data[key], (dict, list))
        if isinstance(data[key], (set, tuple)):
            data[key] = list(data[key])
            value_is_collection = True
        if white_list is not None and key in white_list:
            masked_data[key] = data[key]
        elif masking_on or key in masking_fields:
            if value_is_collection:
                # если глубина не превышена, идем внутрь с включенным флагом и уменьшаем глубину
                if masking_on and depth_level > 0:
                    masked_data[key] = _masking(data[key], masking_fields, depth_level - 1,
                                                mask_available_depth, masking_on=True, white_list=white_list)
                elif key in masking_fields and masking_fields[key] > 0:
                    masked_data[key] = _masking(data[key], masking_fields, masking_fields[key] - 1,
                                                mask_available_depth, masking_on=True, white_list=white_list)
                else:
                    counter = structure_mask(data[key], depth=1, available_depth=mask_available_depth)
                    masked_data[key] = f'*items-{counter.items}*collections-{counter.collections}*maxdepth-{counter.max_depth}*'  # noqa
            elif data[key] is not None:  # в случае простого элемента. маскируем как ***
                masked_data[key] = '***'
            else:
                masked_data[key] = data[key]
        elif key in CARD_MASKING_FIELDS or card_masking_on:  # проверка на реквизиты карты
            if value_is_collection:
                masked_data[key] = _masking(data[key], masking_fields, depth_level, mask_available_depth,
                                            masking_on, card_masking_on=True, white_list=white_list)
            elif isinstance(data[key], str):
                masked_data[key] = card_regular.sub(card_sub_func, data[key])
            elif isinstance(data[key], int):
                str_value = str(data[key])
                masked_value = card_regular.sub(card_sub_func, str_value)
                if masked_value != str_value:
                    masked_data[key] = masked_value
                else:
                    masked_data[key] = data[key]
            else:
                masked_data[key] = data[key]
        elif value_is_collection:
            # если маскировка не нужна уходим глубже без включенного флага
            masked_data[key] = _masking(data[key], masking_fields, depth_level, mask_available_depth,
                                        masking_on=False, card_masking_on=card_masking_on, white_list=white_list)
        else:
            masked_data[key] = data[key]
    return masked_data


def structure_mask(data: Union[Dict, List], depth: int, available_depth: int = -1,
                   counter: Optional[Counter] = None):
    """
    Функция маскирования для сложной структуры
    :param data: структура маскируемая без сохранения структуры
    :param depth: текущая глубина вложенности
    :param available_depth: максимальная глубина прохода, при -1 глубина не ограничена
    :param counter: объект счетчик
    :return: counter с подсчитанными элементами
    """
    # в зависимости от листа или словаря создаем итератор
    if isinstance(data, dict):
        key_gen = data.items()
    else:
        key_gen = enumerate(data)

    if counter is None:
        counter = Counter()

    for key, _ in key_gen:
        if isinstance(data[key], (dict, list)):
            counter.collections += 1
            # если встречаем коллекцию и глубина не превышена идем внутрь
            if depth < available_depth or available_depth == -1:
                structure_mask(data[key], depth + 1, available_depth, counter)
        else:
            # если элемент простой крутим счетчик простых элементов
            counter.items += 1
            if depth > counter.max_depth:
                counter.max_depth = depth

    return counter

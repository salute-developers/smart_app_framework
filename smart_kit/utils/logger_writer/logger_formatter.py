# coding: utf-8
from datetime import datetime
from numbers import Number
from typing import Any, Dict, Optional

from pythonjsonlogger import jsonlogger
import logging
from core.model.factory import build_factory
from core.model.registered import Registered
from smart_kit.configs.settings import Settings


def to_num(s):
    try:
        return int(s)
    except ValueError:
        return float(s)


TYPES = {
    "str": str,
    "dict": dict,
    "int": Number,
    "bool": bool,
}

TYPE_CASTS = {
    "str": str,
    "dict": dict,
    "int": to_num,
    "bool": bool,
}


loggers_formatter = Registered()
loggers_formatter_factory = build_factory(loggers_formatter)


class SmartKitJsonFormatter(jsonlogger.JsonFormatter):
    VERSION = 0
    NLPF_VERSION = 0
    DEV_TEAM = "NA"
    APPLICATION_NAME = "NA"

    def __init__(self, *args, **kwargs):
        self.fields_type: dict = kwargs.pop("fields_type", None)
        super().__init__(*args, **kwargs)

    def add_fields(self, log_record, record, message_dict):
        super(SmartKitJsonFormatter, self).add_fields(log_record, record, message_dict)
        dt = datetime.fromtimestamp(record.created)
        st = dt.strftime("%Y-%m-%dT%H:%M:%S")
        log_record["timestamp"] = "%s.%06d" % (st, (record.created - int(record.created)) * 1e6)
        log_record["version"] = self.VERSION
        log_record["nlpf_version"] = self.NLPF_VERSION
        log_record["team"] = self.DEV_TEAM
        log_record["application"] = self.APPLICATION_NAME
        if settings := Settings.get_instance():
            log_record["environment"] = settings.get("template_settings").get("environment")
        if isinstance(record.args, dict):
            log_record["args"] = self._check_fields(record.args)

    def _check_fields(self, record_args: Dict[str, Any], types: Optional[Dict[str, dict]] = None):
        if types is None:
            types = self.fields_type
        if types is None:
            return record_args

        new_args = {}
        for k, v in record_args.items():
            if k not in types or v is None:  # скипаем проверку если поля нет в конфиге, или value = None
                new_args[k] = v
                continue
            if types[k]["type"] == "dict":  # отдельно рекурсивно обрабатываем словари
                if not isinstance(v, dict):  # преобразуем в строку в новое поле, если тип не соответсвует
                    new_args[f"{k}__str"] = str(v)
                    continue
                new_args[k] = self._check_fields(v, types[k]["fields"])
                continue
            if isinstance(v, TYPES[types[k]["type"]]):  # noqa
                new_args[k] = v
                continue

            # пытаемся кастануть тип
            try:
                new_args[k] = TYPE_CASTS[types[k]["type"]](v)
            except (ValueError, TypeError):
                new_args[f"{k}__str"] = str(v)

        return new_args

    def format(self, record: logging.LogRecord) -> str:
        # В готовый json логов добавляем поле с размером json-а.
        result = super(SmartKitJsonFormatter, self).format(record)
        log_size = len(result)
        # Убираем последнюю закрывающую скобку и добавляем поле log_size и закрываем скобки
        return f'{result[:-1]},"log_size":{log_size}}}'

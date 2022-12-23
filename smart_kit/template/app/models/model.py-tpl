from smart_kit.models.smartapp_model import SmartAppModel

from app.handlers.handlers import CustomHandler


class CustomModel(SmartAppModel):
    """Модель сопоставляет обработчики для типов входящих сообщений

    Для использования данной модели присвойте переменной MODEL в app_config этот класс как значение.
    """
    # additional_handlers format:
    # {"MESSAGE_NAME": {"handler": HandlerText, "params": {"dialogue_manager": custom_dialogue_manager}}}
    # "params" are passed as kwargs (after app_name) to handler.__init__(), optional
    additional_handlers = {"CUSTOM_MESSAGE_NAME": {"handler": CustomHandler, "params": {}}}

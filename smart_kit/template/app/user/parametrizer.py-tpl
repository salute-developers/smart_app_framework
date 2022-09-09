from scenarios.user.parametrizer import Parametrizer


class CustomParametrizer(Parametrizer):
    """Параметризатор определяет данные, которые будут доступны в jinja-вставках в языке фреймворка

    Для использования данного параметризатора присвойте переменной PARAMETRIZER в app_config этот класс как значение.
    """
    def __init__(self, user, items):
        super().__init__(user, items)

    def _get_user_data(self, text_preprocessing_result=None):
        data = super()._get_user_data(text_preprocessing_result)
        data.update({})
        return data

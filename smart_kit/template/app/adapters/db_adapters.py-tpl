from core.db_adapter.db_adapter import DBAdapter
from core.db_adapter import error


class CustomDBAdapter(DBAdapter):
    """Класс-коннектор к базе данных

    Может быть использован, например, для загрузки данных о User.

    Ненужные методы можно оставить с телом raise error.NotSupportedOperation.
    """
    def __init__(self, config):
        super().__init__(config)

    def connect(self):
        pass

    def _open(self, filename, *args, **kwargs):
        pass

    def _save(self, id, data):
        pass

    def _replace_if_equals(self, id, sample, data):
        pass

    def _get(self, id):
        pass

    def _list_dir(self, path):
        raise error.NotSupportedOperation

    def _glob(self, path, pattern):
        raise error.NotSupportedOperation

    def _path_exists(self, path):
        pass

    def _on_prepare(self):
        pass

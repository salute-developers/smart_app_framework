from core.db_adapter.db_adapter import AsyncDBAdapter
from copy import copy
from cachetools import TTLCache
from core.db_adapter import error


class MemoryAdapter(AsyncDBAdapter):
    IS_ASYNC = True
    MEM_CACHE_SIZE = 250 * 1024 * 1024
    TTL = 12 * 60 * 60

    def __init__(self, config=None):
        super(AsyncDBAdapter, self).__init__(config)
        config = self.config or {}
        self.init_params = copy(config.get("init_params", {}))
        self.init_params["getsizeof"] = len
        self.init_params.setdefault("maxsize", self.MEM_CACHE_SIZE)
        self.init_params.setdefault("ttl", self.TTL)
        self.memory_storage = TTLCache(**self.init_params)

    async def _glob(self, path, pattern):
        raise error.NotSupportedOperation

    async def _path_exists(self, path):
        raise error.NotSupportedOperation

    async def _on_prepare(self):
        pass

    async def connect(self):
        pass

    async def _open(self, filename, *args, **kwargs):
        pass

    async def _save(self, id, data):
        self.memory_storage[id] = data

    async def _replace_if_equals(self, id, sample, data):
        stored_data = self.memory_storage.get(id)
        if stored_data == sample:
            self.memory_storage[id] = data
            return True
        return False

    async def _get(self, id):
        data = self.memory_storage.get(id)
        return data

    async def _list_dir(self, path):
        pass

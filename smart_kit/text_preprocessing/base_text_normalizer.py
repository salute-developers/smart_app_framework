from collections.abc import Sequence

from smart_kit.utils.cache import Cache


class BaseTextNormalizer:
    TEXT_PARAM_NAME = "text"
    PREPROCESS_METHOD = "preprocess"
    CLASSIFY_METHOD = "classify"
    NORMALIZE_METHOD = "normalize"
    CACHE = Cache

    def load_everything(self) -> None:
        raise NotImplementedError

    def with_cache(self, *args, **kwargs) -> 'BaseTextNormalizer':
        raise NotImplementedError

    def normalize_sequence(self, texts: Sequence, batch_size) -> list:
        raise NotImplementedError

    def __call__(self, text: str):
        raise NotImplementedError

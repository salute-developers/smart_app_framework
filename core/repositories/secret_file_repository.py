import collections.abc

from core.repositories.file_repository import FileRepository, UpdatableFileRepository
from core.repositories.items_repository import ItemsRepository


class SecretFileRepository(ItemsRepository):
    def __init__(
            self,
            filename,
            secret_filename,
            loader,
            source=None,
            save_target=None,
            save_target_secret=None,
            saver=None,
            *args,
            **kwargs,
    ):
        super().__init__(source=source, *args, **kwargs)
        self.file_repository = FileRepository(filename, loader, source, save_target, saver)
        self.secret_file_repository = FileRepository(secret_filename, loader, source, save_target, saver)
        self.save_target = save_target
        self.save_target_secret = save_target_secret
        self.saver = saver

    def update(self, d, u):
        for k, v in u.items():
            if isinstance(v, collections.abc.Mapping):
                d[k] = self.update(d.get(k, {}), v)
            else:
                d[k] = v
        return d

    def load(self):
        self.file_repository.load()
        self.secret_file_repository.load()
        file_repository_data = self.file_repository.data
        secret_file_repository_data = self.secret_file_repository.data
        data = self.update(file_repository_data, secret_file_repository_data)
        self.fill(data)

    def save(self, save_parameters):
        with self.source.open(self.save_target, "wb") as stream:
            stream.write(self.saver(self.file_repository.data, **save_parameters).encode())
        with self.source.open(self.save_target_secret, "wb") as stream:
            stream.write(self.saver(self.secret_file_repository.data, **save_parameters).encode())


class SecretUpdatableFileRepository(SecretFileRepository):
    def __init__(
            self,
            filename,
            secret_filename,
            loader,
            source=None,
            save_target=None,
            save_target_secret=None,
            saver=None,
            *args,
            **kwargs,
    ):
        super(SecretFileRepository, self).__init__(source=source, *args, **kwargs)
        self.file_repository = UpdatableFileRepository(filename, loader, source, save_target, saver)
        self.secret_file_repository = UpdatableFileRepository(secret_filename, loader, source, save_target, saver)
        self.save_target = save_target
        self.save_target_secret = save_target_secret
        self.saver = saver

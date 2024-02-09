import os

from core.repositories.folder_filename_key_repository import FolderFilenameKeyRepository


class PayloadSchemaRepository(FolderFilenameKeyRepository):
    def _save_to_repo(self, repo, shard_path, shard_data):
        path = os.path.relpath(shard_path, self.path)
        repo[path if path.startswith("/") else f"/{path}"] = shard_data

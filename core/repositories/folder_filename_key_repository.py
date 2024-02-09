import os
from core.repositories.folder_repository import FolderRepository


class FolderFilenameKeyRepository(FolderRepository):

    def _form_file_upload_map(self, shard_desc):
        filename_to_data = {}
        for shard in shard_desc:
            shard_data = self._load_item(shard)
            if shard_data:
                self._save_to_repo(filename_to_data, shard, shard_data)
        return filename_to_data

    def _save_to_repo(self, repo, shard_path, shard_data):
        repo[os.path.basename(shard_path).split(".")[0]] = shard_data

    def fill(self, data):
        self.data = data

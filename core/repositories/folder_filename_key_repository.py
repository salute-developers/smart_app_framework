import os
from core.repositories.folder_repository import FolderRepository


class FolderFilenameKeyRepository(FolderRepository):

    def _form_file_upload_map(self, shard_desc):
        filename_to_data = {}
        for shard in shard_desc:
            shard_data = self._load_item(shard)
            if shard_data:
                filename_to_data[os.path.relpath(shard, self.path)] = shard_data
                filename_to_data[os.path.relpath(shard, self.path).split(".")[0]] = shard_data
        return filename_to_data

    def fill(self, data):
        self.data = data

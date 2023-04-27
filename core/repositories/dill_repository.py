# coding: utf-8
import sys
from pathlib import Path

import dill

import core.logging.logger_constants as log_const
from core.logging.logger_utils import log
from core.repositories.base_repository import BaseRepository


class DillRepository(BaseRepository):
    """
    load unpickleable file
    Args:
        filename: path to the file
        source: file adapter e.g OSAdapter, CephAdapter etc
        required: raise FileNotFoundError if file not found
    """
    def __init__(self, filename, source=None, required=True, *args, **kwargs):
        super(DillRepository, self).__init__(source=source, *args, **kwargs)
        self.filename = Path(filename)
        self.required = required

    def load(self):
        dill._dill._reverse_typemap['ClassType'] = type
        try:
            py_version = sys.version_info
            py_suffix = f"_py{py_version.major}{py_version.minor}"
            py_version_resolved_filename = (
                self.filename.parent / f"{self.filename.stem}{py_suffix}{self.filename.suffix}"
            )
            with self.source.open(py_version_resolved_filename, 'rb') as stream:
                data = dill.load(stream)
                self.fill(data)
        except FileNotFoundError as error:
            params = {
                'error': str(error),
                log_const.KEY_NAME: log_const.EXCEPTION_VALUE
            }
            log('DillRepository.load loading failed. Error %(error)s', params=params, level='WARNING')
            if self.required:
                raise
        super(DillRepository, self).load()

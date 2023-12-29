import os
from functools import lru_cache

from hbutils.system import TemporaryDirectory as _OriginTemporaryDirectory


@lru_cache()
def _create_tmp_dir(dir_):
    if dir_:
        os.makedirs(dir_, exist_ok=True)


class TemporaryDirectory(_OriginTemporaryDirectory):
    # noinspection PyShadowingBuiltins
    def __init__(self, suffix=None, prefix=None, dir=None, ignore_cleanup_errors=False):
        dir = dir or os.environ.get('TMPDIR') or None
        _create_tmp_dir(dir)
        _OriginTemporaryDirectory.__init__(self, suffix, prefix, dir, ignore_cleanup_errors)

import os

from hbutils.system import TemporaryDirectory as _OriginTemporaryDirectory


class TemporaryDirectory(_OriginTemporaryDirectory):
    # noinspection PyShadowingBuiltins
    def __init__(self, suffix=None, prefix=None, dir=None, ignore_cleanup_errors=False):
        dir = dir or os.environ.get('TMPDIR')
        _OriginTemporaryDirectory.__init__(self, suffix, prefix, dir, ignore_cleanup_errors)

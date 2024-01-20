import os
from typing import Optional

from .base import register_archive_type

try:
    import rarfile
except ImportError:  # pragma: no cover
    rarfile = None


def _rar_pack(directory, zip_file, silent: bool = False, clear: bool = False):
    _ = directory, zip_file, silent, clear
    raise RuntimeError('RAR format packing is not supported.')


def _rar_unpack(rar_file, directory, silent: bool = False, password: Optional[str] = None):
    _ = silent
    directory = os.fspath(directory)
    os.makedirs(directory, exist_ok=True)
    with rarfile.RarFile(rar_file, 'r') as zf:
        if password is not None:
            zf.setpassword(password)
        zf.extractall(directory)


if rarfile is not None:
    register_archive_type('rar', ['.rar'], _rar_pack, _rar_unpack)

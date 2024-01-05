import os.path
import zipfile
from typing import Optional

from .base import register_archive_type
from ..utils import tqdm, walk_files

try:
    import zlib

    del zlib
    _ZLIB_SUPPORTED = True
except ImportError:
    _ZLIB_SUPPORTED = False


def _zip_pack(directory, zip_file, silent: bool = False, clear: bool = False):
    with zipfile.ZipFile(zip_file, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        progress = tqdm(walk_files(directory), silent=silent, desc=f'Packing {directory!r} ...')
        for file in progress:
            progress.set_description(file)
            zf.write(os.path.join(directory, file), file)
            if clear:
                os.remove(os.path.join(directory, file))


def _zip_unpack(zip_file, directory, silent: bool = False, password: Optional[str] = None):
    directory = os.fspath(directory)
    os.makedirs(directory, exist_ok=True)
    with zipfile.ZipFile(zip_file, 'r') as zf:
        if password is not None:
            zf.setpassword(password.encode(encoding='utf-8'))
        progress = tqdm(zf.namelist(), silent=silent, desc=f'Unpacking {directory!r} ...')
        for zipinfo in progress:
            progress.set_description(zipinfo)
            zf.extract(zipinfo, directory)


if _ZLIB_SUPPORTED:
    register_archive_type('zip', ['.zip'], _zip_pack, _zip_unpack)

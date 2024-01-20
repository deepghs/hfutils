import os
from typing import Optional

from .base import register_archive_type
from ..utils import tqdm, walk_files

try:
    import py7zr
except ImportError:  # pragma: no cover
    py7zr = None


def _7z_pack(directory, sz_file, silent: bool = False, clear: bool = False):
    with py7zr.SevenZipFile(sz_file, 'w') as zf:
        progress = tqdm(walk_files(directory), silent=silent, desc=f'Packing {directory!r} ...')
        for file in progress:
            progress.set_description(file)
            zf.write(os.path.join(directory, file), file)
            if clear:
                os.remove(os.path.join(directory, file))


def _7z_unpack(sz_file, directory, silent: bool = False, password: Optional[str] = None):
    _ = silent
    directory = os.fspath(directory)
    os.makedirs(directory, exist_ok=True)
    with py7zr.SevenZipFile(sz_file, 'r', password=password) as zf:
        zf.extractall(directory)


if py7zr is not None:
    register_archive_type('7z', ['.7z'], _7z_pack, _7z_unpack)

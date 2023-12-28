import os

from .base import register_archive_type
from ..utils import tqdm, walk_files

try:
    import py7zr
except ImportError:  # pragma: no cover
    py7zr = None


def _7z_pack(directory, sz_file, silent: bool = False):
    with py7zr.SevenZipFile(sz_file, 'w') as zf:
        progress = tqdm(walk_files(directory), silent=silent, desc=f'Packing {directory!r} ...')
        for file in progress:
            progress.set_description(file)
            zf.write(os.path.join(directory, file), file)


def _7z_unpack(sz_file, directory, silent: bool = False):
    directory = os.fspath(directory)
    os.makedirs(directory, exist_ok=True)
    with py7zr.SevenZipFile(sz_file, 'r') as zf:
        progress = tqdm(zf.getnames(), silent=silent, desc=f'Unpacking {directory!r} ...')
        for name in progress:
            progress.set_description(name)
            zf.extract(path=directory, targets=[name])
            zf.reset()


if py7zr is not None:
    register_archive_type('7z', ['.7z'], _7z_pack, _7z_unpack)

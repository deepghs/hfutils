import os

from .base import register_archive_type
from ..utils import tqdm

try:
    import rarfile
except ImportError:  # pragma: no cover
    rarfile = None


def _rar_pack(directory, zip_file, silent: bool = False):
    _ = directory, zip_file, silent
    raise RuntimeError('RAR format packing is not supported.')


def _rar_unpack(rar_file, directory, silent: bool = False):
    directory = os.fspath(directory)
    os.makedirs(directory, exist_ok=True)
    with rarfile.RarFile(rar_file, 'r') as zf:
        progress = tqdm(zf.namelist(), silent=silent, desc=f'Unpacking {directory!r} ...')
        for rarinfo in progress:
            progress.set_description(rarinfo)
            zf.extract(rarinfo, directory)


if rarfile is not None:
    register_archive_type('rar', ['.rar'], _rar_pack, _rar_unpack)

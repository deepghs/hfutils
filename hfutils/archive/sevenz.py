"""
This module provides functionality for handling 7z archive files.

It includes functions for packing and unpacking 7z archives, and registers
the 7z archive type if the py7zr library is available.

.. note::
    `py7zr` is required for 7z archive operations. If not available, 7z functionality will be disabled.
"""

import os
from typing import Optional

from .base import register_archive_type
from ..utils import tqdm, walk_files

try:
    import py7zr
except ImportError:  # pragma: no cover
    py7zr = None


def _7z_pack(directory, sz_file, pattern: Optional[str] = None, silent: bool = False, clear: bool = False):
    """
    Pack files from a directory into a 7z archive.

    :param directory: The source directory containing files to be packed.
    :type directory: str
    :param sz_file: The path to the output 7z file.
    :type sz_file: str
    :param pattern: Optional file pattern to filter files for packing.
    :type pattern: str, optional
    :param silent: If True, suppress progress output.
    :type silent: bool, optional
    :param clear: If True, remove source files after packing.
    :type clear: bool, optional
    """
    with py7zr.SevenZipFile(sz_file, 'w') as zf:
        progress = tqdm(walk_files(directory, pattern=pattern), silent=silent, desc=f'Packing {directory!r} ...')
        for file in progress:
            progress.set_description(file)
            zf.write(os.path.join(directory, file), file)
            if clear:
                os.remove(os.path.join(directory, file))


def _7z_unpack(sz_file, directory, silent: bool = False, password: Optional[str] = None):
    """
    Unpack files from a 7z archive to a directory.

    :param sz_file: The path to the 7z file to be unpacked.
    :type sz_file: str
    :param directory: The destination directory for unpacked files.
    :type directory: str
    :param silent: If True, suppress progress output (currently unused).
    :type silent: bool, optional
    :param password: Optional password for encrypted archives.
    :type password: str, optional
    """
    _ = silent
    directory = os.fspath(directory)
    os.makedirs(directory, exist_ok=True)
    with py7zr.SevenZipFile(sz_file, 'r', password=password) as zf:
        zf.extractall(directory)


if py7zr is not None:
    register_archive_type('7z', ['.7z'], _7z_pack, _7z_unpack)

"""
This module provides functionality for working with ZIP archives.

It includes functions for packing directories into ZIP files and unpacking ZIP files into directories.
The module also registers the ZIP archive type if zlib compression is supported.
"""

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


def _zip_pack(directory, zip_file, pattern: Optional[str] = None, silent: bool = False, clear: bool = False):
    """
    Pack a directory into a ZIP file.

    :param directory: The directory to pack.
    :type directory: str
    :param zip_file: The path to the output ZIP file.
    :type zip_file: str
    :param pattern: Optional file pattern to filter files for packing.
    :type pattern: str, optional
    :param silent: If True, suppress progress output.
    :type silent: bool
    :param clear: If True, remove original files after packing.
    :type clear: bool
    """
    with zipfile.ZipFile(zip_file, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        progress = tqdm(walk_files(directory, pattern=pattern), silent=silent, desc=f'Packing {directory!r} ...')
        for file in progress:
            progress.set_description(file)
            zf.write(os.path.join(directory, file), file)
            if clear:
                os.remove(os.path.join(directory, file))


def _zip_unpack(zip_file, directory, silent: bool = False, password: Optional[str] = None):
    """
    Unpack a ZIP file into a directory.

    :param zip_file: The path to the ZIP file to unpack.
    :type zip_file: str
    :param directory: The directory to unpack the ZIP file into.
    :type directory: str
    :param silent: If True, suppress progress output.
    :type silent: bool
    :param password: Optional password for encrypted ZIP files.
    :type password: str, optional
    """
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

"""
This module provides functionality for handling RAR archives.

It includes functions for unpacking RAR files and a placeholder for packing (which is not supported).
The module uses the 'rarfile' library for RAR file operations.

.. note::
    The 'rarfile' library is optional. If not installed, RAR functionality will be limited.
"""

import os
from typing import Optional

from .base import register_archive_type

try:
    import rarfile
except ImportError:  # pragma: no cover
    rarfile = None


def _rar_pack(directory, zip_file, pattern: Optional[str] = None, silent: bool = False, clear: bool = False):
    """
    Placeholder function for RAR packing (not supported).

    :param directory: The directory to pack.
    :param zip_file: The output RAR file.
    :param pattern: Optional pattern for file selection.
    :type pattern: str, optional
    :param silent: If True, suppress output. Defaults to False.
    :type silent: bool
    :param clear: If True, clear the directory after packing. Defaults to False.
    :type clear: bool
    :raises RuntimeError: Always raised as RAR packing is not supported.
    """
    _ = directory, zip_file, pattern, silent, clear
    raise RuntimeError('RAR format packing is not supported.')


def _rar_unpack(rar_file, directory, silent: bool = False, password: Optional[str] = None):
    """
    Unpack a RAR file to a specified directory.

    :param rar_file: The RAR file to unpack.
    :param directory: The directory to unpack the RAR file into.
    :param silent: If True, suppress output. Defaults to False.
    :type silent: bool
    :param password: Optional password for encrypted RAR files.
    :type password: str, optional
    """
    _ = silent
    directory = os.fspath(directory)
    os.makedirs(directory, exist_ok=True)
    with rarfile.RarFile(rar_file, 'r') as zf:
        if password is not None:
            zf.setpassword(password)
        zf.extractall(directory)


if rarfile is not None:
    register_archive_type('rar', ['.rar'], _rar_pack, _rar_unpack)

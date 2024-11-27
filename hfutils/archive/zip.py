"""
This module provides functionality for working with ZIP archives.

It includes functions for packing directories into ZIP files and unpacking ZIP files into directories.
The module also registers the ZIP archive type if zlib compression is supported.
"""

import os.path
import zipfile
from typing import Optional

from .base import register_archive_type, ArchiveWriter
from ..utils import tqdm, walk_files

try:
    import zlib

    del zlib
    _ZLIB_SUPPORTED = True
except ImportError:
    _ZLIB_SUPPORTED = False


class ZipWriter(ArchiveWriter):
    """
    A specialized archive writer for ZIP files.

    This class extends the base ArchiveWriter to provide ZIP-specific functionality,
    implementing the ZIP_DEFLATED compression method for file writing.

    Methods:
        _create_handler: Creates a new ZIP file handler
        _add_file: Adds a file to the ZIP archive
    """

    def _create_handler(self):
        """
        Create a new ZIP file handler with deflate compression.

        :return: A ZipFile instance configured for writing with compression
        :rtype: zipfile.ZipFile
        """
        return zipfile.ZipFile(self.archive_file, "w", compression=zipfile.ZIP_DEFLATED)

    def _add_file(self, filename: str, arcname: str):
        """
        Add a file to the ZIP archive.

        :param filename: The path to the file to add
        :type filename: str
        :param arcname: The name to give the file within the archive
        :type arcname: str
        :return: None
        """
        return self._handler.write(filename, arcname)


def _zip_pack(directory, zip_file, pattern: Optional[str] = None, silent: bool = False, clear: bool = False):
    """
    Pack a directory into a ZIP file.

    This function creates a ZIP archive containing all files from the specified directory.
    It supports file filtering through patterns and can optionally remove source files
    after successful packing.

    :param directory: The directory to pack
    :type directory: str
    :param zip_file: The path to the output ZIP file
    :type zip_file: str
    :param pattern: Optional file pattern to filter files for packing
    :type pattern: str, optional
    :param silent: If True, suppress progress output
    :type silent: bool
    :param clear: If True, remove original files after packing
    :type clear: bool
    """
    with ZipWriter(zip_file) as zf:
        progress = tqdm(walk_files(directory, pattern=pattern),
                        silent=silent, desc=f'Packing {directory!r} ...')
        for file in progress:
            progress.set_description(file)
            zf.add(os.path.join(directory, file), file)
            if clear:
                os.remove(os.path.join(directory, file))


def _zip_unpack(zip_file, directory, silent: bool = False, password: Optional[str] = None):
    """
    Unpack a ZIP file into a directory.

    This function extracts all contents of a ZIP file into the specified directory.
    It supports password-protected archives and provides progress tracking during extraction.

    :param zip_file: The path to the ZIP file to unpack
    :type zip_file: str
    :param directory: The directory to unpack the ZIP file into
    :type directory: str
    :param silent: If True, suppress progress output
    :type silent: bool
    :param password: Optional password for encrypted ZIP files
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
    register_archive_type('zip', ['.zip'], _zip_pack, _zip_unpack, ZipWriter)

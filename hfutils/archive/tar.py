"""
This module provides functionality for working with tar archive files.

It includes functions for packing and unpacking tar archives with various compression options.
The module also registers different tar archive types based on the available compression libraries.

.. note::
    Some compression methods may not be available depending on the system's installed libraries.
"""

import copy
import os.path
import tarfile
import warnings
from functools import partial
from typing import Literal, Optional

from .base import register_archive_type, ArchiveWriter
from .zip import _ZLIB_SUPPORTED
from ..utils import walk_files, tqdm

try:
    import bz2

    del bz2
    _BZ2_SUPPORTED = True
except ImportError:
    _BZ2_SUPPORTED = False

try:
    import lzma

    del lzma
    _LZMA_SUPPORTED = True
except ImportError:
    _LZMA_SUPPORTED = False

CompressTyping = Literal['', 'gzip', 'bzip2', 'xz']


class TarWriter(ArchiveWriter):
    """
    A class for writing tar archive files with various compression options.

    This class extends ArchiveWriter to provide specific functionality for
    creating tar archives with different compression methods.

    :param archive_file: Path to the tar archive file to be created
    :type archive_file: str
    :param compress: Compression method to use
    :type compress: CompressTyping
    :raises ValueError: If an unsupported compression method is specified

    Usage::

        with TarWriter('archive.tar.gz', compress='gzip') as tar:
            tar.add('file.txt', 'file.txt')
    """

    def __init__(self, archive_file: str, compress: CompressTyping = "gzip"):
        """
        Initialize a new TarWriter instance.

        :param archive_file: Path to the tar archive file to be created
        :type archive_file: str
        :param compress: Compression method to use ('', 'gzip', 'bzip2', 'xz')
        :type compress: CompressTyping
        :raises ValueError: If an unsupported compression method is specified
        """
        super().__init__(archive_file)
        if compress is None:
            self._tar_compression = ''
        elif compress == 'gzip':
            self._tar_compression = 'gz'
        elif compress == 'bzip2':
            self._tar_compression = 'bz2'
        elif compress == 'xz':
            self._tar_compression = 'xz'
        else:
            raise ValueError("bad value for 'compress', or compression format not "
                             "supported : {0}".format(compress))

    def _create_handler(self):
        """
        Create and return a tarfile handler for writing.

        :return: A tarfile handler object
        :rtype: tarfile.TarFile
        """
        return tarfile.open(self.archive_file, f'w|{self._tar_compression}')

    def _add_file(self, filename: str, arcname: str):
        """
        Add a file to the tar archive.

        :param filename: Path to the file to add
        :type filename: str
        :param arcname: Name to give the file in the archive
        :type arcname: str
        """
        return self._handler.add(filename, arcname)


def _tarfile_pack(directory, tar_file, pattern: Optional[str] = None,
                  compress: CompressTyping = "gzip", silent: bool = False, clear: bool = False):
    """
    Pack a directory into a tar archive file with optional compression.

    This function walks through the specified directory and creates a tar archive
    containing all matching files. It supports various compression methods and
    can optionally remove source files after packing.

    :param directory: The directory to pack
    :type directory: str
    :param tar_file: The name of the tar file to create
    :type tar_file: str
    :param pattern: Optional file pattern to filter files for packing
    :type pattern: str, optional
    :param compress: Compression method to use ('', 'gzip', 'bzip2', 'xz')
    :type compress: CompressTyping
    :param silent: If True, suppress progress output
    :type silent: bool
    :param clear: If True, remove packed files from the source directory
    :type clear: bool
    :raises ValueError: If an unsupported compression method is specified
    """
    with TarWriter(tar_file, compress=compress) as tar:
        progress = tqdm(walk_files(directory, pattern=pattern), silent=silent, desc=f'Packing {directory!r} ...')
        for file in progress:
            progress.set_description(file)
            tar.add(os.path.join(directory, file), file)
            if clear:
                os.remove(os.path.join(directory, file))


def _tarfile_unpack(tar_file, directory, silent: bool = False, numeric_owner=False, password: Optional[str] = None):
    """
    Unpack a tar archive file into a directory.

    This function extracts all files from a tar archive while preserving file
    attributes and handling directory permissions properly. It supports progress
    tracking and can handle various compression formats automatically.

    :param tar_file: The tar file to unpack
    :type tar_file: str
    :param directory: The directory to unpack the files into
    :type directory: str
    :param silent: If True, suppress progress output
    :type silent: bool
    :param numeric_owner: If True, use numeric owner (UID, GID) instead of names
    :type numeric_owner: bool
    :param password: Ignored for tar files (included for compatibility with other archive types)
    :type password: str, optional
    """
    if password is not None:
        warnings.warn('Password is not supported in tar archive files.\n'
                      'So assigned password will be ignored.')
    with tarfile.open(tar_file) as tar:
        directories = []
        progress = tqdm(tar, silent=silent, desc=f'Unpacking {directory!r} ...')
        for tarinfo in progress:
            progress.set_description(tarinfo.name)
            if tarinfo.isdir():
                # Extract directories with a safe mode.
                directories.append(tarinfo)
                tarinfo = copy.copy(tarinfo)
                tarinfo.mode = 0o700
            # Do not set_attrs directories, as we will do that further down
            tar.extract(tarinfo, directory, set_attrs=not tarinfo.isdir(),
                        numeric_owner=numeric_owner)

        # Reverse sort directories.
        directories.sort(key=lambda a: a.name)
        directories.reverse()

        # Set correct owner, mtime and filemode on directories.
        progress = tqdm(directories, silent=silent, desc=f'Applying directories ...')
        for tarinfo in progress:
            progress.set_description(tarinfo.name)
            dirpath = os.path.join(directory, tarinfo.name)
            tar.chown(tarinfo, dirpath, numeric_owner=numeric_owner)
            tar.utime(tarinfo, dirpath)
            tar.chmod(tarinfo, dirpath)


# Register various tar archive types based on available compression libraries
register_archive_type(
    'tar', ['.tar'],
    partial(_tarfile_pack, compress=None),
    _tarfile_unpack,
    partial(TarWriter, compress=None),
)
if _ZLIB_SUPPORTED:
    register_archive_type(
        'gztar', ['.tar.gz', '.tgz'],
        partial(_tarfile_pack, compress='gzip'),
        _tarfile_unpack,
        partial(TarWriter, compress='gzip'),
    )
if _BZ2_SUPPORTED:
    register_archive_type(
        'bztar', ['.tar.bz2', '.tbz2'],
        partial(_tarfile_pack, compress='bzip2'),
        _tarfile_unpack,
        partial(TarWriter, compress='bzip2'),
    )
if _LZMA_SUPPORTED:
    register_archive_type(
        'xztar', ['.tar.xz', '.txz'],
        partial(_tarfile_pack, compress='xz'),
        _tarfile_unpack,
        partial(TarWriter, compress='xz'),
    )

"""
This module provides functionality for handling archive files in various formats.

It includes functions for registering custom archive types, packing directories into archives,
unpacking archives, and determining archive types based on file extensions. The module supports
a flexible system for working with different archive formats through a registration mechanism.

.. note::
    This module uses a global dictionary to store registered archive types, so it's
    important to register custom types before using the packing and unpacking functions.
"""

import os.path
import warnings
from typing import List, Dict, Tuple, Callable, Optional


class ArchiveWriter:
    """
    A base class for creating archive writers.

    This class provides a context manager interface for handling archive files,
    allowing files to be added to the archive and ensuring proper resource management.

    :param archive_file: The path to the archive file to be created or modified.
    :type archive_file: str
    """

    def __init__(self, archive_file: str):
        self.archive_file = archive_file
        self._handler = None

    def _create_handler(self):
        """
        Create the handler for the archive writer.

        This method should be overridden by subclasses to provide specific
        handler creation logic for different archive types.

        :raises NotImplementedError: If not overridden in a subclass.
        """
        raise NotImplementedError  # pragma: no cover

    def _add_file(self, filename: str, arcname: str):
        """
        Add a file to the archive.

        This method should be overridden by subclasses to define how files
        are added to the archive for different formats.

        :param filename: The path to the file to add to the archive.
        :type filename: str
        :param arcname: The archive name for the file.
        :type arcname: str
        :raises NotImplementedError: If not overridden in a subclass.
        """
        raise NotImplementedError  # pragma: no cover

    def open(self):
        """
        Open the archive for writing.

        Initializes the handler if it has not been created yet.
        """
        if self._handler is None:
            self._handler = self._create_handler()

    def add(self, filename: str, arcname: str):
        """
        Add a file to the archive.

        :param filename: The path to the file to add.
        :type filename: str
        :param arcname: The name to use for the file within the archive.
        :type arcname: str
        """
        return self._add_file(filename, arcname)

    def close(self):
        """
        Close the archive.

        Ensures that all resources are properly released.
        """
        if self._handler is not None:
            self._handler.close()
            self._handler = None

    def __enter__(self):
        """
        Enter the runtime context related to this object.

        Opens the archive for writing.
        """
        self.open()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        Exit the runtime context related to this object.

        Closes the archive, ensuring that resources are released.
        """
        self.close()


_FN_WRITER = Callable[[str], ArchiveWriter]
_KNOWN_ARCHIVE_TYPES: Dict[str, Tuple[List[str], Callable, Callable, _FN_WRITER]] = {}


def register_archive_type(name: str, exts: List[str], fn_pack: Callable, fn_unpack: Callable, fn_writer: _FN_WRITER):
    """
    Register a custom archive type with associated file extensions and packing/unpacking functions.

    This function allows users to add support for new archive types by providing the necessary
    information and functions to handle the archive format.

    :param name: The name of the archive type (e.g., 'zip', 'tar').
    :type name: str
    :param exts: A list of file extensions associated with the archive type (e.g., ['.zip']).
    :type exts: List[str]
    :param fn_pack: The packing function that takes a directory and an archive filename as input and creates an archive.
    :type fn_pack: Callable
    :param fn_unpack: The unpacking function that takes an archive filename and a directory as input and extracts the archive.
    :type fn_unpack: Callable
    :param fn_writer: The writer creation function that takes an archive filename and creates an archive writer object.
    :type fn_writer: Callable[[str], ArchiveWriter]
    :raises ValueError: If no file extensions are provided for the archive type.

    Example:
        >>> def custom_pack(directory, archive_file, **kwargs):
        ...     # Custom packing logic here
        ...     pass
        >>> def custom_unpack(archive_file, directory, **kwargs):
        ...     # Custom unpacking logic here
        ...     pass
        >>> register_archive_type('custom', ['.cst'], custom_pack, custom_unpack)
    """
    if len(exts) == 0:
        raise ValueError(f'At least one extension name for archive type {name!r} should be provided.')
    _KNOWN_ARCHIVE_TYPES[name] = (exts, fn_pack, fn_unpack, fn_writer)


def get_archive_extname(type_name: str) -> str:
    """
    Get the file extension associated with a registered archive type.

    This function returns the first (primary) file extension associated with the given archive type.

    :param type_name: The name of the archive type.
    :type type_name: str
    :return: The file extension associated with the archive type.
    :rtype: str
    :raises ValueError: If the archive type is not registered.

    Example:
        >>> get_archive_extname('zip')
        '.zip'
    """
    if type_name in _KNOWN_ARCHIVE_TYPES:
        exts, _, _, _ = _KNOWN_ARCHIVE_TYPES[type_name]
        return exts[0]
    else:
        raise ValueError(f'Unknown archive type - {type_name!r}.')


def archive_pack(type_name: str, directory: str, archive_file: str,
                 pattern: Optional[str] = None, silent: bool = False, clear: bool = False):
    """
    Pack a directory into an archive file using the specified archive type.

    This function creates an archive of the specified type containing the contents of the given directory.

    :param type_name: The name of the archive type.
    :type type_name: str
    :param directory: The directory to pack.
    :type directory: str
    :param archive_file: The filename of the resulting archive.
    :type archive_file: str
    :param pattern: A pattern to filter files for inclusion in the archive (optional).
    :type pattern: str, optional
    :param silent: If True, suppress warnings during the packing process.
    :type silent: bool
    :param clear: If True, remove existing files when packing.
    :type clear: bool
    :raises ValueError: If the archive type is not registered.

    Example:
        >>> archive_pack('zip', '/path/to/directory', '/path/to/archive.zip', pattern='*.txt')
    """
    exts, fn_pack, _, _ = _KNOWN_ARCHIVE_TYPES[type_name]
    if not any(os.path.normcase(archive_file).endswith(extname) for extname in exts):
        warnings.warn(f'The archive type {type_name!r} should be one of the {exts!r}, '
                      f'but file name {archive_file!r} is assigned. '
                      f'We strongly recommend using a regular extension name for the archive file.')

    return fn_pack(directory, archive_file, pattern=pattern, silent=silent, clear=clear)


def get_archive_type(archive_file: str) -> str:
    """
    Determine the archive type based on the file extension.

    This function examines the file extension of the given archive file and returns the
    corresponding archive type name.

    :param archive_file: The filename of the archive.
    :type archive_file: str
    :return: The name of the archive type.
    :rtype: str
    :raises ValueError: If the file extension is not associated with any registered archive type.

    Example:
        >>> get_archive_type('/path/to/archive.tar.gz')
        'gztar'
    """
    archive_file = os.path.normcase(archive_file)
    for type_name, (exts, _, _, _) in _KNOWN_ARCHIVE_TYPES.items():
        if any(archive_file.endswith(extname) for extname in exts):
            return type_name

    raise ValueError(f'Unknown type of archive file {archive_file!r}.')


def archive_unpack(archive_file: str, directory: str, silent: bool = False, password: Optional[str] = None):
    """
    Unpack an archive file into a directory using the specified archive type.

    This function extracts the contents of the given archive file into the specified directory.

    :param archive_file: The filename of the archive.
    :type archive_file: str
    :param directory: The directory to unpack the contents into.
    :type directory: str
    :param silent: If True, suppress warnings during the unpacking process.
    :type silent: bool
    :param password: The password to extract the archive file (optional).
    :type password: str, optional
    :raises ValueError: If the archive type is not recognized.

    Example:
        >>> archive_unpack('/path/to/archive.zip', '/path/to/extract')
    """
    type_name = get_archive_type(archive_file)
    _, _, fn_unpack, _ = _KNOWN_ARCHIVE_TYPES[type_name]
    return fn_unpack(archive_file, directory, silent=silent, password=password)


def archive_writer(type_name: str, archive_file: str) -> ArchiveWriter:
    """
    Create an ArchiveWriter instance for the specified archive type.

    This function returns an ArchiveWriter that can be used to add files to an archive.

    :param type_name: The name of the archive type.
    :type type_name: str
    :param archive_file: The filename of the archive to be created or modified.
    :type archive_file: str
    :return: An ArchiveWriter instance for the specified archive type.
    :rtype: ArchiveWriter
    :raises ValueError: If the archive type is not registered.

    Example:
        >>> writer = archive_writer('zip', '/path/to/archive.zip')
        >>> with writer as w:
        ...     w.add('/path/to/file.txt', 'file.txt')
    """
    exts, _, _, fn_writer = _KNOWN_ARCHIVE_TYPES[type_name]
    if not any(os.path.normcase(archive_file).endswith(extname) for extname in exts):
        warnings.warn(f'The archive type {type_name!r} should be one of the {exts!r}, '
                      f'but file name {archive_file!r} is assigned. '
                      f'We strongly recommend using a regular extension name for the archive file.')

    return fn_writer(archive_file)

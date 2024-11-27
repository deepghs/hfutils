"""
Archive handling module for managing different types of archive files.

.. note::
    This module uses a global dictionary to store registered archive types, so it's
    important to register custom types before using the packing and unpacking functions.
"""

import os.path
import warnings
from functools import lru_cache
from typing import List, Dict, Tuple, Callable, Optional

from hfutils.utils import splitext_with_composite


class ArchiveWriter:
    """
    Base class for creating and managing archive writers.

    This class provides a context manager interface for handling archive files,
    allowing for safe resource management and consistent file addition operations.
    It serves as a template for specific archive format implementations.

    :param archive_file: Path to the archive file to be created or modified.
    :type archive_file: str

    Example:
        >>> with ArchiveWriter('output.zip') as writer:
        ...     writer.add('file.txt', 'archive_path/file.txt')
    """

    def __init__(self, archive_file: str):
        self.archive_file = archive_file
        self._handler = None

    def _create_handler(self):
        """
        Create the underlying archive handler.

        This method should be implemented by subclasses to initialize the
        specific archive format handler.

        :raises NotImplementedError: When called on the base class.
        """
        raise NotImplementedError  # pragma: no cover

    def _add_file(self, filename: str, arcname: str):
        """
        Add a file to the archive.

        This method should be implemented by subclasses to define the
        specific file addition logic for each archive format.

        :param filename: Path to the file to be added.
        :type filename: str
        :param arcname: Desired path within the archive.
        :type arcname: str
        :raises NotImplementedError: When called on the base class.
        """
        raise NotImplementedError  # pragma: no cover

    def open(self):
        """
        Open the archive for writing.

        Initializes the archive handler if it hasn't been created yet.
        This method is automatically called when using the context manager.
        """
        if self._handler is None:
            self._handler = self._create_handler()

    def add(self, filename: str, arcname: str):
        """
        Add a file to the archive.

        :param filename: Path to the file to be added.
        :type filename: str
        :param arcname: Desired path within the archive.
        :type arcname: str
        """
        return self._add_file(filename, arcname)

    def close(self):
        """
        Close the archive and release resources.

        This method ensures proper cleanup of resources and is automatically
        called when using the context manager.
        """
        if self._handler is not None:
            self._handler.close()
            self._handler = None

    def __enter__(self):
        """
        Context manager entry point.

        :return: Self reference for use in context manager.
        :rtype: ArchiveWriter
        """
        self.open()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        Context manager exit point.

        Ensures proper cleanup of resources when exiting the context.

        :param exc_type: Exception type if an error occurred.
        :param exc_val: Exception value if an error occurred.
        :param exc_tb: Exception traceback if an error occurred.
        """
        self.close()


_FN_WRITER = Callable[[str], ArchiveWriter]
_KNOWN_ARCHIVE_TYPES: Dict[str, Tuple[List[str], Callable, Callable, _FN_WRITER]] = {}


def register_archive_type(name: str, exts: List[str], fn_pack: Callable, fn_unpack: Callable, fn_writer: _FN_WRITER):
    """
    Register a new archive type with its associated handlers and extensions.

    This function allows for the registration of custom archive formats by providing
    the necessary functions for packing, unpacking, and creating archive writers.

    :param name: Identifier for the archive type (e.g., 'zip', 'tar').
    :type name: str
    :param exts: List of file extensions for this archive type (e.g., ['.zip']).
    :type exts: List[str]
    :param fn_pack: Function to create archives of this type.
    :type fn_pack: Callable
    :param fn_unpack: Function to extract archives of this type.
    :type fn_unpack: Callable
    :param fn_writer: Function to create an archive writer instance.
    :type fn_writer: Callable[[str], ArchiveWriter]
    :raises ValueError: If no file extensions are provided.

    Example:
        >>> def my_pack(directory, archive_file, **kwargs): pass
        >>> def my_unpack(archive_file, directory, **kwargs): pass
        >>> def my_writer(archive_file): return CustomWriter(archive_file)
        >>> register_archive_type('custom', ['.cst'], my_pack, my_unpack, my_writer)
    """
    if len(exts) == 0:
        raise ValueError(f'At least one extension name for archive type {name!r} should be provided.')
    _KNOWN_ARCHIVE_TYPES[name] = (exts, fn_pack, fn_unpack, fn_writer)


def get_archive_extname(type_name: str) -> str:
    """
    Retrieve the primary file extension for a registered archive type.

    :param type_name: Name of the archive type.
    :type type_name: str
    :return: Primary file extension for the archive type.
    :rtype: str
    :raises ValueError: If the archive type is not registered.

    Example:
        >>> ext = get_archive_extname('zip')
        >>> print(ext)
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
    Create an archive from a directory using the specified archive type.

    :param type_name: Name of the archive type to use.
    :type type_name: str
    :param directory: Source directory to archive.
    :type directory: str
    :param archive_file: Output archive file path.
    :type archive_file: str
    :param pattern: Optional file pattern for filtering (e.g., '*.txt').
    :type pattern: str, optional
    :param silent: Whether to suppress warnings.
    :type silent: bool
    :param clear: Whether to remove existing files when packing.
    :type clear: bool
    :raises ValueError: If the archive type is not registered.

    Example:
        >>> archive_pack('zip', '/data', 'backup.zip', pattern='*.dat', silent=True)
    """
    exts, fn_pack, _, _ = _KNOWN_ARCHIVE_TYPES[type_name]
    if not any(os.path.normcase(archive_file).endswith(extname) for extname in exts):
        warnings.warn(f'The archive type {type_name!r} should be one of the {exts!r}, '
                      f'but file name {archive_file!r} is assigned. '
                      f'We strongly recommend using a regular extension name for the archive file.')

    return fn_pack(directory, archive_file, pattern=pattern, silent=silent, clear=clear)


def get_archive_type(archive_file: str) -> str:
    """
    Determine the archive type from a file's extension.

    :param archive_file: Path to the archive file.
    :type archive_file: str
    :return: Name of the detected archive type.
    :rtype: str
    :raises ValueError: If the file extension doesn't match any registered type.

    Example:
        >>> type_name = get_archive_type('data.tar.gz')
        >>> print(type_name)
        'gztar'
    """
    archive_file = os.path.normcase(archive_file)
    for type_name, (exts, _, _, _) in _KNOWN_ARCHIVE_TYPES.items():
        if any(archive_file.endswith(extname) for extname in exts):
            return type_name

    raise ValueError(f'Unknown type of archive file {archive_file!r}.')


def archive_unpack(archive_file: str, directory: str, silent: bool = False, password: Optional[str] = None):
    """
    Extract an archive file to a directory.

    :param archive_file: Path to the archive file to extract.
    :type archive_file: str
    :param directory: Destination directory for extraction.
    :type directory: str
    :param silent: Whether to suppress warnings.
    :type silent: bool
    :param password: Optional password for protected archives.
    :type password: str, optional
    :raises ValueError: If the archive type is not recognized.

    Example:
        >>> archive_unpack('protected.zip', 'output_dir', password='secret')
    """
    type_name = get_archive_type(archive_file)
    _, _, fn_unpack, _ = _KNOWN_ARCHIVE_TYPES[type_name]
    return fn_unpack(archive_file, directory, silent=silent, password=password)


def archive_writer(type_name: str, archive_file: str) -> ArchiveWriter:
    """
    Create an archive writer for the specified archive type.

    :param type_name: Name of the archive type.
    :type type_name: str
    :param archive_file: Path to the archive file to create.
    :type archive_file: str
    :return: An archive writer instance.
    :rtype: ArchiveWriter
    :raises ValueError: If the archive type is not registered.

    Example:
        >>> with archive_writer('zip', 'output.zip') as writer:
        ...     writer.add('file.txt', 'docs/file.txt')
    """
    exts, _, _, fn_writer = _KNOWN_ARCHIVE_TYPES[type_name]
    if not any(os.path.normcase(archive_file).endswith(extname) for extname in exts):
        warnings.warn(f'The archive type {type_name!r} should be one of the {exts!r}, '
                      f'but file name {archive_file!r} is assigned. '
                      f'We strongly recommend using a regular extension name for the archive file.')

    return fn_writer(archive_file)


@lru_cache()
def _get_all_extensions():
    """
    Get a list of all registered archive extensions.

    :return: List of all registered file extensions.
    :rtype: list
    """
    extensions = []
    for type_name, (exts, _, _, _) in _KNOWN_ARCHIVE_TYPES.items():
        extensions.extend(exts)
    return extensions


def archive_splitext(filename: str) -> Tuple[str, str]:
    """
    Split a filename into root and extension, handling compound extensions.

    :param filename: The filename to split.
    :type filename: str
    :return: Tuple of (root, extension).
    :rtype: Tuple[str, str]

    Example:
        >>> root, ext = archive_splitext('data.tar.gz')
        >>> print(root, ext)
        'data' '.tar.gz'
    """
    return splitext_with_composite(filename, _get_all_extensions())

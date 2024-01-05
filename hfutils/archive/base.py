import os.path
import warnings
from typing import List, Dict, Tuple, Callable, Optional

_KNOWN_ARCHIVE_TYPES: Dict[str, Tuple[List[str], Callable, Callable]] = {}


def register_archive_type(name: str, exts: List[str], fn_pack: Callable, fn_unpack: Callable):
    """
    Register a custom archive type with associated file extensions and packing/unpacking functions.

    :param name: The name of the archive type.
    :type name: str
    :param exts: A list of file extensions associated with the archive type.
    :type exts: List[str]
    :param fn_pack: The packing function that takes a directory and an archive filename as input and creates an archive.
    :type fn_pack: Callable
    :param fn_unpack: The unpacking function that takes an archive filename and a directory as input and extracts the archive.
    :type fn_unpack: Callable
    """
    if len(exts) == 0:
        raise ValueError(f'At least one extension name for archive type {name!r} should be provided.')
    _KNOWN_ARCHIVE_TYPES[name] = (exts, fn_pack, fn_unpack)


def get_archive_extname(type_name: str) -> str:
    """
    Get the file extension associated with a registered archive type.

    :param type_name: The name of the archive type.
    :type type_name: str

    :return: The file extension associated with the archive type.
    :rtype: str
    :raises ValueError: If the archive type is not registered.
    """
    if type_name in _KNOWN_ARCHIVE_TYPES:
        exts, _, _ = _KNOWN_ARCHIVE_TYPES[type_name]
        return exts[0]
    else:
        raise ValueError(f'Unknown archive type - {type_name!r}.')


def archive_pack(type_name: str, directory: str, archive_file: str, silent: bool = False, clear: bool = False):
    """
    Pack a directory into an archive file using the specified archive type.

    :param type_name: The name of the archive type.
    :type type_name: str
    :param directory: The directory to pack.
    :type directory: str
    :param archive_file: The filename of the resulting archive.
    :type archive_file: str
    :param silent: If True, suppress warnings during the packing process.
    :type silent: bool
    :param clear: If True, remove existing files when packing.
    :type clear: bool

    :return: The path to the created archive file.
    :rtype: str
    """
    exts, fn_pack, _ = _KNOWN_ARCHIVE_TYPES[type_name]
    if not any(os.path.normcase(archive_file).endswith(extname) for extname in exts):
        warnings.warn(f'The archive type {type_name!r} should be one of the {exts!r}, '
                      f'but file name {archive_file!r} is assigned. '
                      f'We strongly recommend using a regular extension name for the archive file.')

    return fn_pack(directory, archive_file, silent=silent, clear=clear)


def get_archive_type(archive_file: str) -> str:
    """
    Determine the archive type based on the file extension.

    :param archive_file: The filename of the archive.
    :type archive_file: str

    :return: The name of the archive type.
    :rtype: str
    :raises ValueError: If the file extension is not associated with any registered archive type.
    """
    archive_file = os.path.normcase(archive_file)
    for type_name, (exts, _, _) in _KNOWN_ARCHIVE_TYPES.items():
        if any(archive_file.endswith(extname) for extname in exts):
            return type_name

    raise ValueError(f'Unknown type of archive file {archive_file!r}.')


def archive_unpack(archive_file: str, directory: str, silent: bool = False, password: Optional[str] = None):
    """
    Unpack an archive file into a directory using the specified archive type.

    :param archive_file: The filename of the archive.
    :type archive_file: str
    :param directory: The directory to unpack the contents into.
    :type directory: str
    :param silent: If True, suppress warnings during the unpacking process.
    :type silent: bool
    :param password: The password to extract the archive file.
    :type password: str, optional

    :return: The path to the unpacked directory.
    :rtype: str
    """
    type_name = get_archive_type(archive_file)
    _, _, fn_unpack = _KNOWN_ARCHIVE_TYPES[type_name]
    return fn_unpack(archive_file, directory, silent=silent, password=password)

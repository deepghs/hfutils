import os.path
import warnings
from typing import List, Dict, Tuple, Callable

_KNOWN_ARCHIVE_TYPES: Dict[str, Tuple[List[str], Callable, Callable]] = {}


def register_archive_type(name: str, exts: List[str], fn_pack: Callable, fn_unpack: Callable):
    if len(exts) == 0:
        raise ValueError(f'At least one extension name for archive type {name!r} should be provided.')
    _KNOWN_ARCHIVE_TYPES[name] = (exts, fn_pack, fn_unpack)


def get_archive_extname(type_name: str) -> str:
    if type_name in _KNOWN_ARCHIVE_TYPES:
        exts, _, _ = _KNOWN_ARCHIVE_TYPES[type_name]
        return exts[0]
    else:
        raise ValueError(f'Unknown archive type - {type_name!r}.')


def archive_pack(type_name: str, directory: str, archive_file: str, silent: bool = False):
    exts, fn_pack, _ = _KNOWN_ARCHIVE_TYPES[type_name]
    if not any(os.path.normcase(archive_file).endswith(extname) for extname in exts):
        warnings.warn(f'The archive type {type_name!r} should be one of the {exts!r}, '
                      f'but file name {archive_file!r} is assigned. '
                      f'We Strongly recommend you to use a regular extension name for archive file.')

    return fn_pack(directory, archive_file, silent=silent)


def get_archive_type(archive_file: str) -> str:
    archive_file = os.path.normcase(archive_file)
    for type_name, (exts, _, _) in _KNOWN_ARCHIVE_TYPES.items():
        if any(archive_file.endswith(extname) for extname in exts):
            return type_name

    raise ValueError(f'Unknown tyep of archive file {archive_file!r}.')


def archive_unpack(archive_file: str, directory, silent: bool = False):
    type_name = get_archive_type(archive_file)
    _, _, fn_unpack = _KNOWN_ARCHIVE_TYPES[type_name]
    return fn_unpack(archive_file, directory, silent=silent)

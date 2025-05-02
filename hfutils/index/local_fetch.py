"""
This module provides utility functions for working with tar archives and their associated index files.
It includes functions for retrieving archive indexes, listing files, checking file existence,
getting file information, and downloading files from archives.

The module relies on a JSON-based index file that contains metadata about the files within the archive,
including their offsets, sizes, and optional SHA256 hashes.

Functions in this module are designed to work with both local archive files and their corresponding
index files, providing a convenient interface for archive manipulation and file extraction.
"""

import json
import os
from hashlib import sha256
from typing import Optional, List, Tuple, BinaryIO

from cachetools import LRUCache
from hbutils.scale import size_to_bytes_str

_TAR_IDX_CACHE = LRUCache(maxsize=192)


def _tar_get_cache_key(archive_file: str, idx_file: Optional[str] = None) -> Tuple[str, Optional[int], Optional[int]]:
    """
    Generate a cache key for the tar index file.

    :param archive_file: Path to the tar archive file.
    :type archive_file: str
    :param idx_file: Optional path to the index file. If not provided,
                    a default index file path will be generated.
    :type idx_file: Optional[str]

    :return: The normalized cache key path.
    :rtype: Tuple[str, Optional[int], Optional[int]]

    :example:
        >>> key = _tar_get_cache_key('archive.tar', 'index.json')
    """
    body, _ = os.path.splitext(archive_file)
    default_index_file = f'{body}.json'
    idx_file = idx_file or default_index_file
    idx_file = os.path.realpath(os.path.expanduser(idx_file))
    idx_file = os.path.normcase(os.path.normpath(idx_file))

    if os.path.exists(idx_file):
        stat = os.stat(idx_file)
        mtime, size = int(stat.st_mtime), int(stat.st_size)
    else:
        mtime, size = None, None

    return idx_file, mtime, size


def tar_get_index(archive_file: str, idx_file: Optional[str] = None, no_cache: bool = False):
    """
    Retrieve the index data for a given tar archive file.

    This function reads the JSON index file associated with the archive,
    which contains metadata about the files within the archive.

    :param archive_file: Path to the tar archive file.
    :type archive_file: str
    :param idx_file: Optional path to the index file. If not provided,
                     it will be inferred from the archive file name.
    :type idx_file: Optional[str]
    :param no_cache: Whether to bypass the cache and force a new index file reading.
    :type no_cache: bool

    :return: The parsed JSON data from the index file.
    :rtype: dict

    :raises FileNotFoundError: If the index file is not found.
    :raises json.JSONDecodeError: If the index file is not valid JSON.

    :example:
        >>> index_data = tar_get_index('my_archive.tar')
    """
    cache_key = _tar_get_cache_key(
        archive_file=archive_file,
        idx_file=idx_file,
    )
    idx_file, _, _ = cache_key

    if not no_cache and cache_key in _TAR_IDX_CACHE:
        return _TAR_IDX_CACHE[cache_key]
    else:
        with open(idx_file, 'r') as f:
            idx_data = json.load(f)
        _TAR_IDX_CACHE[cache_key] = idx_data
        return idx_data


_TAR_IDX_PFILES_CACHE = LRUCache(maxsize=192)


def _tar_get_processed_files(archive_file: str, idx_file: Optional[str] = None, no_cache: bool = False):
    """
    Get processed files information from the tar archive index.

    This internal function processes the raw index data and returns a processed
    version of the files information, utilizing caching for performance.

    :param archive_file: Path to the tar archive file.
    :type archive_file: str
    :param idx_file: Optional path to the index file.
    :type idx_file: Optional[str]
    :param no_cache: Whether to bypass the cache and force reprocessing.
    :type no_cache: bool

    :return: Processed files information dictionary.
    :rtype: dict

    :example:
        >>> files = _tar_get_processed_files('archive.tar')
    """
    cache_key = _tar_get_cache_key(archive_file=archive_file, idx_file=idx_file)
    if not no_cache and cache_key in _TAR_IDX_PFILES_CACHE:
        return _TAR_IDX_PFILES_CACHE[cache_key]
    else:
        from .fetch import _hf_files_process
        index = tar_get_index(
            archive_file=archive_file,
            idx_file=idx_file,
            no_cache=no_cache,
        )
        files = _hf_files_process(index['files'])
        _TAR_IDX_PFILES_CACHE[cache_key] = files
        return files


def tar_list_files(archive_file: str, idx_file: Optional[str] = None, no_cache: bool = False) -> List[str]:
    """
    List all files contained within the specified tar archive.

    This function uses the archive's index file to retrieve the list of files
    without actually reading the tar archive itself.

    :param archive_file: Path to the tar archive file.
    :type archive_file: str
    :param idx_file: Optional path to the index file. If not provided,
                     it will be inferred from the archive file name.
    :type idx_file: Optional[str]
    :param no_cache: Whether to bypass the cache and force a new index file reading.
    :type no_cache: bool

    :return: A list of file names contained in the archive.
    :rtype: List[str]

    :example:
        >>> files = tar_list_files('my_archive.tar')
        >>> for file in files:
        >>>     print(file)
    """
    index_data = tar_get_index(
        archive_file=archive_file,
        idx_file=idx_file,
        no_cache=no_cache,
    )
    return list(index_data['files'].keys())


def tar_file_exists(archive_file: str, file_in_archive: str,
                    idx_file: Optional[str] = None, no_cache: bool = False) -> bool:
    """
    Check if a specific file exists within the tar archive.

    This function uses the archive's index to check for file existence
    without reading the entire archive.

    :param archive_file: Path to the tar archive file.
    :type archive_file: str
    :param file_in_archive: The name of the file to check for in the archive.
    :type file_in_archive: str
    :param idx_file: Optional path to the index file. If not provided,
                     it will be inferred from the archive file name.
    :type idx_file: Optional[str]
    :param no_cache: Whether to bypass the cache and force a new index file reading.
    :type no_cache: bool

    :return: True if the file exists in the archive, False otherwise.
    :rtype: bool

    :example:
        >>> exists = tar_file_exists('my_archive.tar', 'path/to/file.txt')
        >>> if exists:
        >>>     print("File exists in the archive")
    """
    from .fetch import _n_path
    files = _tar_get_processed_files(
        archive_file=archive_file,
        idx_file=idx_file,
        no_cache=no_cache,
    )
    return _n_path(file_in_archive) in files


def tar_file_info(archive_file: str, file_in_archive: str,
                  idx_file: Optional[str] = None, no_cache: bool = False) -> dict:
    """
    Retrieve information about a specific file within the tar archive.

    This function returns a dictionary containing metadata about the specified file,
    such as its size and offset within the archive.

    :param archive_file: Path to the tar archive file.
    :type archive_file: str
    :param file_in_archive: The name of the file to get information for.
    :type file_in_archive: str
    :param idx_file: Optional path to the index file. If not provided,
                     it will be inferred from the archive file name.
    :type idx_file: Optional[str]
    :param no_cache: Whether to bypass the cache and force a new index file reading.
    :type no_cache: bool

    :return: A dictionary containing file metadata.
    :rtype: dict

    :raises FileNotFoundError: If the specified file is not found in the archive.

    :example:
        >>> info = tar_file_info('my_archive.tar', 'path/to/file.txt')
        >>> print(f"File size: {info['size']} bytes")
    """
    from .fetch import _n_path
    files = _tar_get_processed_files(
        archive_file=archive_file,
        idx_file=idx_file,
        no_cache=no_cache,
    )
    if _n_path(file_in_archive) not in files:
        raise FileNotFoundError(f'File {file_in_archive!r} not found '
                                f'in local archive {archive_file!r}.')
    else:
        return files[_n_path(file_in_archive)]


def tar_file_size(archive_file: str, file_in_archive: str, idx_file: Optional[str] = None) -> int:
    """
    Get the size of a specific file within the tar archive.

    This function returns the size of the specified file in bytes.

    :param archive_file: Path to the tar archive file.
    :type archive_file: str
    :param file_in_archive: The name of the file to get the size for.
    :type file_in_archive: str
    :param idx_file: Optional path to the index file. If not provided,
                     it will be inferred from the archive file name.
    :type idx_file: Optional[str]

    :return: The size of the file in bytes.
    :rtype: int

    :raises FileNotFoundError: If the specified file is not found in the archive.

    :example:
        >>> size = tar_file_size('my_archive.tar', 'path/to/file.txt')
        >>> print(f"File size: {size} bytes")
    """
    return tar_file_info(
        archive_file=archive_file,
        file_in_archive=file_in_archive,
        idx_file=idx_file,
    )['size']


def _tar_file_info_write(archive_file: str, info: dict, file_to_write: BinaryIO,
                         chunk_size: int = 1 << 20, no_validate: bool = False):
    """
    Internal function to write file contents from the archive to a file object.

    This function handles the actual reading from the archive and writing to the
    destination, including validation of file size and hash if required.

    :param archive_file: Path to the tar archive file.
    :type archive_file: str
    :param info: Dictionary containing file metadata.
    :type info: dict
    :param file_to_write: File object to write the contents to.
    :type file_to_write: BinaryIO
    :param chunk_size: Size of chunks to read/write at a time.
    :type chunk_size: int
    :param no_validate: Whether to skip validation of size and hash.
    :type no_validate: bool

    :raises ArchiveStandaloneFileIncompleteDownload: If the file size doesn't match expected.
    :raises ArchiveStandaloneFileHashNotMatch: If the file hash doesn't match expected.
    """
    from .fetch import ArchiveStandaloneFileIncompleteDownload, ArchiveStandaloneFileHashNotMatch
    start_pos = file_to_write.tell()
    file_sha = sha256() if not no_validate and info.get('sha256') else None
    if info['size'] > 0:
        with open(archive_file, 'rb') as rf:
            rf.seek(info['offset'])
            tp = info['offset'] + info['size']
            while rf.tell() < tp:
                read_bytes = min(tp - rf.tell(), chunk_size)
                chunk_data = rf.read(read_bytes)
                file_to_write.write(chunk_data)
                if file_sha is not None:
                    file_sha.update(chunk_data)

    if not no_validate:
        if file_to_write.tell() != start_pos + info['size']:
            raise ArchiveStandaloneFileIncompleteDownload(
                f'Expected size is {size_to_bytes_str(info["size"], sigfigs=4, system="si")}, '
                f'but actually {size_to_bytes_str(file_to_write.tell() - start_pos, sigfigs=4, system="si")} downloaded.'
            )

        if file_sha is not None:
            _sha256 = file_sha.hexdigest()
            if _sha256 != info['sha256']:
                raise ArchiveStandaloneFileHashNotMatch(
                    f'Expected hash is {info["sha256"]!r}, but actually {_sha256!r} found.'
                )


def tar_file_write_bytes(archive_file: str, file_in_archive: str, bin_file: BinaryIO,
                         idx_file: Optional[str] = None, chunk_size: int = 1 << 20, no_cache: bool = False):
    """
    Write the contents of a file from the archive to a binary file object.

    :param archive_file: Path to the tar archive file.
    :type archive_file: str
    :param file_in_archive: Name of the file in the archive to extract.
    :type file_in_archive: str
    :param bin_file: Binary file object to write to.
    :type bin_file: BinaryIO
    :param idx_file: Optional path to the index file.
    :type idx_file: Optional[str]
    :param chunk_size: Size of chunks to read/write at a time.
    :type chunk_size: int
    :param no_cache: Whether to bypass the cache.
    :type no_cache: bool

    :raises FileNotFoundError: If the specified file is not found in the archive.
    """
    from .fetch import _n_path
    files = _tar_get_processed_files(
        archive_file=archive_file,
        idx_file=idx_file,
        no_cache=no_cache,
    )
    if _n_path(file_in_archive) not in files:
        raise FileNotFoundError(f'File {file_in_archive!r} not found '
                                f'in local archive {archive_file!r}.')

    info = files[_n_path(file_in_archive)]
    _tar_file_info_write(
        archive_file=archive_file,
        info=info,
        file_to_write=bin_file,
        chunk_size=chunk_size,
        no_validate=False,
    )


def tar_file_download(archive_file: str, file_in_archive: str, local_file: str,
                      idx_file: Optional[str] = None, chunk_size: int = 1 << 20,
                      force_download: bool = False, no_cache: bool = False):
    """
    Extract and download a specific file from the tar archive to a local file.

    This function reads the specified file from the archive and writes it to a local file.
    It also performs integrity checks to ensure the downloaded file is complete and matches
    the expected hash (if provided in the index).

    :param archive_file: Path to the tar archive file.
    :type archive_file: str
    :param file_in_archive: The name of the file to extract from the archive.
    :type file_in_archive: str
    :param local_file: The path where the extracted file should be saved.
    :type local_file: str
    :param idx_file: Optional path to the index file. If not provided,
                     it will be inferred from the archive file name.
    :type idx_file: Optional[str]
    :param chunk_size: The size of chunks to read and write, in bytes. Default is 1MB.
    :type chunk_size: int
    :param force_download: Force download the file to destination path.
                           Defualt to `False`, downloading will be skipped if the local file
                           is fully matched with expected file.
    :type force_download: bool
    :param no_cache: Whether to bypass the cache and force a new index file reading.
    :type no_cache: bool

    :raises FileNotFoundError: If the specified file is not found in the archive.
    :raises ArchiveStandaloneFileIncompleteDownload: If the downloaded file size doesn't match the expected size.
    :raises ArchiveStandaloneFileHashNotMatch: If the SHA256 hash of the downloaded file doesn't match the expected hash.

    :example:
        >>> tar_file_download('my_archive.tar', 'path/to/file.txt', 'local_file.txt')
    """
    from .fetch import _n_path, _f_sha256, \
        ArchiveStandaloneFileIncompleteDownload, ArchiveStandaloneFileHashNotMatch

    files = _tar_get_processed_files(
        archive_file=archive_file,
        idx_file=idx_file,
        no_cache=no_cache,
    )
    if _n_path(file_in_archive) not in files:
        raise FileNotFoundError(f'File {file_in_archive!r} not found '
                                f'in local archive {archive_file!r}.')

    info = files[_n_path(file_in_archive)]

    if not force_download and os.path.exists(local_file) and \
            os.path.isfile(local_file) and os.path.getsize(local_file) == info['size']:
        _expected_sha256 = info.get('sha256')
        if not _expected_sha256 or _f_sha256(local_file) == _expected_sha256:
            # file already ready, no need to download it again
            return

    if os.path.dirname(local_file):
        os.makedirs(os.path.dirname(local_file), exist_ok=True)
    try:
        with open(local_file, 'wb') as wf:
            _tar_file_info_write(
                archive_file=archive_file,
                info=info,
                file_to_write=wf,
                chunk_size=chunk_size,
                no_validate=True,
            )

        if os.path.getsize(local_file) != info['size']:
            raise ArchiveStandaloneFileIncompleteDownload(
                f'Expected size is {info["size"]}, but actually {os.path.getsize(local_file)} downloaded.'
            )

        if info.get('sha256'):
            _sha256 = _f_sha256(local_file)
            if _sha256 != info['sha256']:
                raise ArchiveStandaloneFileHashNotMatch(
                    f'Expected hash is {info["sha256"]!r}, but actually {_sha256!r} found.'
                )

    except Exception:
        if os.path.exists(local_file):
            os.remove(local_file)
        raise


def tar_cache_reset(maxsize: Optional[int] = None):
    """
    Reset the tar index and processed files caches.

    This function clears both the index cache and processed files cache.
    Optionally, it can also resize the caches.

    :param maxsize: Optional new maximum size for the caches.
                   If provided, both caches will be recreated with this size.
    :type maxsize: Optional[int]

    :example:
        >>> tar_cache_reset(maxsize=256)  # Reset and resize caches
        >>> tar_cache_reset()  # Just clear the existing caches
    """
    global _TAR_IDX_CACHE, _TAR_IDX_PFILES_CACHE
    _TAR_IDX_CACHE.clear()
    _TAR_IDX_PFILES_CACHE.clear()
    if maxsize is not None and _TAR_IDX_CACHE.maxsize != maxsize:
        _TAR_IDX_CACHE = LRUCache(maxsize=maxsize)
        _TAR_IDX_PFILES_CACHE = LRUCache(maxsize=maxsize)

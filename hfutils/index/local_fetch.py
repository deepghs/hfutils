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
from typing import Optional, List


def tar_get_index(archive_file: str, idx_file: Optional[str] = None):
    """
    Retrieve the index data for a given tar archive file.

    This function reads the JSON index file associated with the archive,
    which contains metadata about the files within the archive.

    :param archive_file: Path to the tar archive file.
    :type archive_file: str
    :param idx_file: Optional path to the index file. If not provided,
                     it will be inferred from the archive file name.
    :type idx_file: Optional[str]

    :return: The parsed JSON data from the index file.
    :rtype: dict

    :raises FileNotFoundError: If the index file is not found.
    :raises json.JSONDecodeError: If the index file is not valid JSON.

    :example:
        >>> index_data = tar_get_index('my_archive.tar')
    """
    body, _ = os.path.splitext(archive_file)
    default_index_file = f'{body}.json'
    with open(idx_file or default_index_file, 'r') as f:
        return json.load(f)


def tar_list_files(archive_file: str, idx_file: Optional[str] = None) -> List[str]:
    """
    List all files contained within the specified tar archive.

    This function uses the archive's index file to retrieve the list of files
    without actually reading the tar archive itself.

    :param archive_file: Path to the tar archive file.
    :type archive_file: str
    :param idx_file: Optional path to the index file. If not provided,
                     it will be inferred from the archive file name.
    :type idx_file: Optional[str]

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
    )
    return list(index_data['files'].keys())


def tar_file_exists(archive_file: str, file_in_archive: str, idx_file: Optional[str] = None) -> bool:
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

    :return: True if the file exists in the archive, False otherwise.
    :rtype: bool

    :example:
        >>> exists = tar_file_exists('my_archive.tar', 'path/to/file.txt')
        >>> if exists:
        >>>     print("File exists in the archive")
    """
    from .fetch import _hf_files_process, _n_path
    index = tar_get_index(
        archive_file=archive_file,
        idx_file=idx_file,
    )
    files = _hf_files_process(index['files'])
    return _n_path(file_in_archive) in files


def tar_file_info(archive_file: str, file_in_archive: str, idx_file: Optional[str] = None) -> dict:
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

    :return: A dictionary containing file metadata.
    :rtype: dict

    :raises FileNotFoundError: If the specified file is not found in the archive.

    :example:
        >>> info = tar_file_info('my_archive.tar', 'path/to/file.txt')
        >>> print(f"File size: {info['size']} bytes")
    """
    from .fetch import _hf_files_process, _n_path
    index = tar_get_index(
        archive_file=archive_file,
        idx_file=idx_file,
    )
    files = _hf_files_process(index['files'])
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


def tar_file_download(archive_file: str, file_in_archive: str, local_file: str,
                      idx_file: Optional[str] = None, chunk_size: int = 1 << 20, force_download: bool = False):
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

    :raises FileNotFoundError: If the specified file is not found in the archive.
    :raises ArchiveStandaloneFileIncompleteDownload: If the downloaded file size doesn't match the expected size.
    :raises ArchiveStandaloneFileHashNotMatch: If the SHA256 hash of the downloaded file doesn't match the expected hash.

    :example:
        >>> tar_file_download('my_archive.tar', 'path/to/file.txt', 'local_file.txt')
    """
    from .fetch import _hf_files_process, _n_path, _f_sha256, \
        ArchiveStandaloneFileIncompleteDownload, ArchiveStandaloneFileHashNotMatch

    index = tar_get_index(
        archive_file=archive_file,
        idx_file=idx_file,
    )
    files = _hf_files_process(index['files'])
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
            if info['size'] > 0:
                with open(archive_file, 'rb') as rf:
                    rf.seek(info['offset'])
                    tp = info['offset'] + info['size']
                    while rf.tell() < tp:
                        read_bytes = min(tp - rf.tell(), chunk_size)
                        wf.write(rf.read(read_bytes))

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

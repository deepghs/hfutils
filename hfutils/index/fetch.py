import json
import os.path
import threading
import warnings
from collections import defaultdict
from hashlib import sha256
from typing import Optional, Dict, Union, List, BinaryIO

import huggingface_hub
from cachetools import LRUCache
from hbutils.scale import size_to_bytes_str
from hbutils.testing import vpip
from huggingface_hub import constants
from huggingface_hub.file_download import http_get, hf_hub_url
from huggingface_hub.utils import build_hf_headers
from tqdm import tqdm

from .hash import _f_sha256
from ..operate.base import RepoTypeTyping, get_hf_client
from ..utils import hf_normpath, BinaryProxyIO


class ArchiveStandaloneFileIncompleteDownload(Exception):
    """
    Exception raised when a standalone file in an archive is incompletely downloaded.
    """


class ArchiveStandaloneFileHashNotMatch(Exception):
    """
    Exception raised when the hash of a standalone file in an archive does not match.
    """


_HF_TAR_IDX_LOCKS = defaultdict(threading.Lock)
_HF_TAR_IDX_CACHE = LRUCache(maxsize=192)


def _hf_tar_get_cache_key(repo_id: str, archive_in_repo: str,
                          repo_type: RepoTypeTyping = 'dataset', revision: str = 'main',
                          idx_repo_id: Optional[str] = None, idx_file_in_repo: Optional[str] = None,
                          idx_repo_type: Optional[RepoTypeTyping] = None, idx_revision: Optional[str] = None):
    """
    Generate a cache key for tar archive index.

    :param repo_id: Repository identifier
    :type repo_id: str
    :param archive_in_repo: Path to archive file in repository
    :type archive_in_repo: str
    :param repo_type: Type of repository
    :type repo_type: RepoTypeTyping
    :param revision: Repository revision
    :type revision: str
    :param idx_repo_id: Index repository identifier
    :type idx_repo_id: Optional[str]
    :param idx_file_in_repo: Path to index file
    :type idx_file_in_repo: Optional[str]
    :param idx_repo_type: Index repository type
    :type idx_repo_type: Optional[RepoTypeTyping]
    :param idx_revision: Index repository revision
    :type idx_revision: Optional[str]

    :return: Tuple containing cache key components
    :rtype: tuple
    """
    body, _ = os.path.splitext(archive_in_repo)
    default_index_file = f'{body}.json'
    f_repo_id = idx_repo_id or repo_id
    f_repo_type = idx_repo_type or repo_type
    f_filename = hf_normpath(idx_file_in_repo or default_index_file)
    f_revision = idx_revision or revision

    return f_repo_id, f_repo_type, f_filename, f_revision


def hf_tar_get_index(repo_id: str, archive_in_repo: str,
                     repo_type: RepoTypeTyping = 'dataset', revision: str = 'main',
                     idx_repo_id: Optional[str] = None, idx_file_in_repo: Optional[str] = None,
                     idx_repo_type: Optional[RepoTypeTyping] = None, idx_revision: Optional[str] = None,
                     hf_token: Optional[str] = None, no_cache: bool = False):
    """
    Get the index of a tar archive file in a Hugging Face repository.

    :param repo_id: The identifier of the repository.
    :type repo_id: str
    :param archive_in_repo: The path to the archive file in the repository.
    :type archive_in_repo: str
    :param repo_type: The type of the Hugging Face repository.
    :type repo_type: RepoTypeTyping, optional
    :param revision: The revision of the repository.
    :type revision: str, optional
    :param idx_repo_id: The identifier of the index repository.
    :type idx_repo_id: str, optional
    :param idx_file_in_repo: The path to the index file in the index repository.
    :type idx_file_in_repo: str, optional
    :param idx_repo_type: The type of the index repository.
    :type idx_repo_type: RepoTypeTyping, optional
    :param idx_revision: The revision of the index repository.
    :type idx_revision: str, optional
    :param hf_token: The Hugging Face access token.
    :type hf_token: str, optional
    :param no_cache: Whether to bypass the cache and force a new index file reading.
    :type no_cache: bool
    :return: The index of the tar archive file.
    :rtype: Dict

    Examples::
        >>> from hfutils.index import hf_tar_get_index
        >>>
        >>> idx = hf_tar_get_index(
        ...     repo_id='deepghs/danbooru_newest',
        ...     archive_in_repo='images/0000.tar',
        ... )
        >>> idx.keys()
        dict_keys(['filesize', 'hash', 'hash_lfs', 'files'])
        >>> idx['files'].keys()
        dict_keys(['7507000.jpg', '7506000.jpg', '7505000.jpg', ...])

    .. note::

        Besides, if the tar and index files are in different repositories, you can also use this function to
        get the index information by explicitly assigning the ``idx_repo_id`` argument.

        >>> from hfutils.index import hf_tar_get_index
        >>>
        >>> idx = hf_tar_get_index(
        ...     repo_id='nyanko7/danbooru2023',
        ...     idx_repo_id='deepghs/danbooru2023_index',
        ...     archive_in_repo='original/data-0000.tar',
        ... )
        >>> idx.keys()
        dict_keys(['filesize', 'hash', 'hash_lfs', 'files'])
        >>> idx['files'].keys()
        dict_keys(['./1000.png', './10000.jpg', './100000.jpg', ...])

    """
    hf_client = get_hf_client(hf_token)
    f_repo_id, f_repo_type, f_filename, f_revision = cache_key = _hf_tar_get_cache_key(
        repo_id=repo_id,
        archive_in_repo=archive_in_repo,
        repo_type=repo_type,
        revision=revision,
        idx_repo_id=idx_repo_id,
        idx_file_in_repo=idx_file_in_repo,
        idx_repo_type=idx_repo_type,
        idx_revision=idx_revision
    )
    if not no_cache and cache_key in _HF_TAR_IDX_CACHE:
        return _HF_TAR_IDX_CACHE[cache_key]
    else:
        with _HF_TAR_IDX_LOCKS[cache_key]:
            with open(hf_client.hf_hub_download(
                    repo_id=f_repo_id,
                    repo_type=f_repo_type,
                    filename=f_filename,
                    revision=f_revision,
            ), 'r') as f:
                idx_data = json.load(f)
            _HF_TAR_IDX_CACHE[cache_key] = idx_data
            return idx_data


_HF_TAR_IDX_PFILES_CACHE = LRUCache(maxsize=192)


def _hf_tar_get_processed_files(repo_id: str, archive_in_repo: str,
                                repo_type: RepoTypeTyping = 'dataset', revision: str = 'main',
                                idx_repo_id: Optional[str] = None, idx_file_in_repo: Optional[str] = None,
                                idx_repo_type: Optional[RepoTypeTyping] = None, idx_revision: Optional[str] = None,
                                hf_token: Optional[str] = None, no_cache: bool = False):
    """
    Get processed files from a tar archive's index with caching support.

    :param repo_id: Repository identifier
    :type repo_id: str
    :param archive_in_repo: Path to archive in repository
    :type archive_in_repo: str
    :param repo_type: Repository type
    :type repo_type: RepoTypeTyping
    :param revision: Repository revision
    :type revision: str
    :param idx_repo_id: Index repository identifier
    :type idx_repo_id: Optional[str]
    :param idx_file_in_repo: Path to index file
    :type idx_file_in_repo: Optional[str]
    :param idx_repo_type: Index repository type
    :type idx_repo_type: Optional[RepoTypeTyping]
    :param idx_revision: Index revision
    :type idx_revision: Optional[str]
    :param hf_token: Hugging Face token
    :type hf_token: Optional[str]
    :param no_cache: Whether to bypass cache
    :type no_cache: bool

    :return: Processed files dictionary
    :rtype: Dict
    """
    cache_key = _hf_tar_get_cache_key(
        repo_id=repo_id,
        archive_in_repo=archive_in_repo,
        repo_type=repo_type,
        revision=revision,
        idx_repo_id=idx_repo_id,
        idx_file_in_repo=idx_file_in_repo,
        idx_repo_type=idx_repo_type,
        idx_revision=idx_revision
    )
    if not no_cache and cache_key in _HF_TAR_IDX_PFILES_CACHE:
        return _HF_TAR_IDX_PFILES_CACHE[cache_key]
    else:
        index = hf_tar_get_index(
            repo_id=repo_id,
            archive_in_repo=archive_in_repo,
            repo_type=repo_type,
            revision=revision,

            idx_repo_id=idx_repo_id,
            idx_file_in_repo=idx_file_in_repo,
            idx_repo_type=idx_repo_type,
            idx_revision=idx_revision,

            hf_token=hf_token,
            no_cache=no_cache,
        )
        files = _hf_files_process(index['files'])
        _HF_TAR_IDX_PFILES_CACHE[cache_key] = files
        return files


def hf_tar_list_files(repo_id: str, archive_in_repo: str,
                      repo_type: RepoTypeTyping = 'dataset', revision: str = 'main',
                      idx_repo_id: Optional[str] = None, idx_file_in_repo: Optional[str] = None,
                      idx_repo_type: Optional[RepoTypeTyping] = None, idx_revision: Optional[str] = None,
                      hf_token: Optional[str] = None, no_cache: bool = False) -> List[str]:
    """
    List files inside a tar archive file in a Hugging Face repository.

    :param repo_id: The identifier of the repository.
    :type repo_id: str
    :param archive_in_repo: The path to the archive file in the repository.
    :type archive_in_repo: str
    :param repo_type: The type of the Hugging Face repository.
    :type repo_type: RepoTypeTyping, optional
    :param revision: The revision of the repository.
    :type revision: str, optional
    :param idx_repo_id: The identifier of the index repository.
    :type idx_repo_id: str, optional
    :param idx_file_in_repo: The path to the index file in the index repository.
    :type idx_file_in_repo: str, optional
    :param idx_repo_type: The type of the index repository.
    :type idx_repo_type: RepoTypeTyping, optional
    :param idx_revision: The revision of the index repository.
    :type idx_revision: str, optional
    :param hf_token: The Hugging Face access token.
    :type hf_token: str, optional
    :param no_cache: Whether to bypass the cache and force a new index file reading.
    :type no_cache: bool
    :return: The list of files inside the tar archive.
    :rtype: List[str]

    Examples::
        >>> from hfutils.index import hf_tar_list_files
        >>>
        >>> hf_tar_list_files(
        ...     repo_id='deepghs/danbooru_newest',
        ...     archive_in_repo='images/0000.tar',
        ... )
        ['7507000.jpg', '7506000.jpg', '7505000.jpg', ...]

    .. note::

        Besides, if the tar and index files are in different repositories, you can also use this function to
        list all the files by explicitly assigning the ``idx_repo_id`` argument.

        >>> from hfutils.index import hf_tar_list_files
        >>>
        >>> hf_tar_list_files(
        ...     repo_id='nyanko7/danbooru2023',
        ...     idx_repo_id='deepghs/danbooru2023_index',
        ...     archive_in_repo='original/data-0000.tar',
        ... )
        ['./1000.png', './10000.jpg', './100000.jpg', ...]

    """
    index_data = hf_tar_get_index(
        repo_id=repo_id,
        archive_in_repo=archive_in_repo,
        repo_type=repo_type,
        revision=revision,

        idx_repo_id=idx_repo_id,
        idx_file_in_repo=idx_file_in_repo,
        idx_repo_type=idx_repo_type,
        idx_revision=idx_revision,

        hf_token=hf_token,
        no_cache=no_cache,
    )

    return list(index_data['files'].keys())


def hf_tar_file_exists(repo_id: str, archive_in_repo: str, file_in_archive: str,
                       repo_type: RepoTypeTyping = 'dataset', revision: str = 'main',
                       idx_repo_id: Optional[str] = None, idx_file_in_repo: Optional[str] = None,
                       idx_repo_type: Optional[RepoTypeTyping] = None, idx_revision: Optional[str] = None,
                       hf_token: Optional[str] = None, no_cache: bool = False):
    """
    Check if a file exists inside a tar archive file in a Hugging Face repository.

    :param repo_id: The identifier of the repository.
    :type repo_id: str
    :param archive_in_repo: The path to the archive file in the repository.
    :type archive_in_repo: str
    :param file_in_archive: The path to the file inside the archive.
    :type file_in_archive: str
    :param repo_type: The type of the Hugging Face repository.
    :type repo_type: RepoTypeTyping, optional
    :param revision: The revision of the repository.
    :type revision: str, optional
    :param idx_repo_id: The identifier of the index repository.
    :type idx_repo_id: str, optional
    :param idx_file_in_repo: The path to the index file in the index repository.
    :type idx_file_in_repo: str, optional
    :param idx_repo_type: The type of the index repository.
    :type idx_repo_type: RepoTypeTyping, optional
    :param idx_revision: The revision of the index repository.
    :type idx_revision: str, optional
    :param hf_token: The Hugging Face access token.
    :type hf_token: str, optional
    :param no_cache: Whether to bypass the cache and force a new index file reading.
    :type no_cache: bool
    :return: True if the file exists, False otherwise.
    :rtype: bool

    Examples::
        >>> from hfutils.index import hf_tar_file_exists
        >>>
        >>> hf_tar_file_exists(
        ...     repo_id='deepghs/danbooru_newest',
        ...     archive_in_repo='images/0000.tar',
        ...     file_in_archive='7506000.jpg',
        ... )
        True
        >>> hf_tar_file_exists(
        ...     repo_id='deepghs/danbooru_newest',
        ...     archive_in_repo='images/0000.tar',
        ...     file_in_archive='17506000.jpg',
        ... )
        False

    .. note::

        Besides, if the tar and index files are in different repositories, you can also use this function to
        check the file existence by explicitly assigning the ``idx_repo_id`` argument.

        >>> from hfutils.index import hf_tar_file_exists
        >>>
        >>> hf_tar_file_exists(
        ...     repo_id='nyanko7/danbooru2023',
        ...     idx_repo_id='deepghs/danbooru2023_index',
        ...     archive_in_repo='original/data-0000.tar',
        ...     file_in_archive='1000.png'
        ... )
        True
        >>> hf_tar_file_exists(
        ...     repo_id='nyanko7/danbooru2023',
        ...     idx_repo_id='deepghs/danbooru2023_index',
        ...     archive_in_repo='original/data-0000.tar',
        ...     file_in_archive='10000000001000.png'
        ... )
        False

    """
    files = _hf_tar_get_processed_files(
        repo_id=repo_id,
        archive_in_repo=archive_in_repo,
        repo_type=repo_type,
        revision=revision,

        idx_repo_id=idx_repo_id,
        idx_file_in_repo=idx_file_in_repo,
        idx_repo_type=idx_repo_type,
        idx_revision=idx_revision,

        hf_token=hf_token,
        no_cache=no_cache,
    )
    return _n_path(file_in_archive) in files


def _n_path(path):
    """
    Normalize a file path.

    :param path: The file path to normalize.
    :type path: str
    :return: The normalized file path.
    :rtype: str
    """
    return os.path.normpath(os.path.join('/', path))


def _hf_files_process(files: Dict[str, dict]):
    """
    Normalize file paths in a dictionary of files.

    :param files: The dictionary of files.
    :type files: Dict[str, dict]
    :return: The dictionary of files with normalized paths.
    :rtype: Dict[str, dict]
    """
    return {_n_path(key): value for key, value in files.items()}


def hf_tar_file_info(repo_id: str, archive_in_repo: str, file_in_archive: str,
                     repo_type: RepoTypeTyping = 'dataset', revision: str = 'main',
                     idx_repo_id: Optional[str] = None, idx_file_in_repo: Optional[str] = None,
                     idx_repo_type: Optional[RepoTypeTyping] = None, idx_revision: Optional[str] = None,
                     hf_token: Optional[str] = None, no_cache: bool = False) -> dict:
    """
    Get a file's detailed information in index tars, including offset, sha256 and size.

    :param repo_id: The identifier of the repository.
    :type repo_id: str
    :param archive_in_repo: The path to the archive file in the repository.
    :type archive_in_repo: str
    :param file_in_archive: The path to the file inside the archive.
    :type file_in_archive: str
    :param repo_type: The type of the Hugging Face repository.
    :type repo_type: RepoTypeTyping, optional
    :param revision: The revision of the repository.
    :type revision: str, optional
    :param idx_repo_id: The identifier of the index repository.
    :type idx_repo_id: str, optional
    :param idx_file_in_repo: The path to the index file in the index repository.
    :type idx_file_in_repo: str, optional
    :param idx_repo_type: The type of the index repository.
    :type idx_repo_type: RepoTypeTyping, optional
    :param idx_revision: The revision of the index repository.
    :type idx_revision: str, optional
    :param hf_token: The Hugging Face access token.
    :type hf_token: str, optional
    :param no_cache: Whether to bypass the cache and force a new index file reading.
    :type no_cache: bool
    :return: Return a dictionary object with meta information of this file.
    :rtype: dict
    :raises FileNotFoundError: Raise this when file not exist in tar archive.

    Examples::
        >>> from hfutils.index import hf_tar_file_info
        >>>
        >>> hf_tar_file_info(
        ...     repo_id='deepghs/danbooru_newest',
        ...     archive_in_repo='images/0000.tar',
        ...     file_in_archive='7506000.jpg',
        ... )
        {'offset': 265728, 'size': 435671, 'sha256': 'ef6a4e031fdffb705c8ce2c64e8cb8d993f431a887d7c1c0b1e6fa56e6107fcd'}

    .. note::

        Besides, if the tar and index files are in different repositories, you can also use this function to
        get the file information by explicitly assigning the ``idx_repo_id`` argument.

        >>> from hfutils.index import hf_tar_file_info
        >>>
        >>> hf_tar_file_info(
        ...     repo_id='nyanko7/danbooru2023',
        ...     idx_repo_id='deepghs/danbooru2023_index',
        ...     archive_in_repo='original/data-0000.tar',
        ...     file_in_archive='1000.png'
        ... )
        {'offset': 1024, 'size': 11966, 'sha256': '478d3313860519372f6a75ede287d4a7c18a2d851bbc79b3dd65caff4c716858'}
    """
    files = _hf_tar_get_processed_files(
        repo_id=repo_id,
        archive_in_repo=archive_in_repo,
        repo_type=repo_type,
        revision=revision,

        idx_repo_id=idx_repo_id,
        idx_file_in_repo=idx_file_in_repo,
        idx_repo_type=idx_repo_type,
        idx_revision=idx_revision,

        hf_token=hf_token,
        no_cache=no_cache,
    )
    if _n_path(file_in_archive) not in files:
        raise FileNotFoundError(f'File {file_in_archive!r} not found '
                                f'in {repo_type}s/{repo_id}@{revision}/{archive_in_repo}.')
    else:
        return files[_n_path(file_in_archive)]


def hf_tar_file_size(repo_id: str, archive_in_repo: str, file_in_archive: str,
                     repo_type: RepoTypeTyping = 'dataset', revision: str = 'main',
                     idx_repo_id: Optional[str] = None, idx_file_in_repo: Optional[str] = None,
                     idx_repo_type: Optional[RepoTypeTyping] = None, idx_revision: Optional[str] = None,
                     hf_token: Optional[str] = None) -> int:
    """
    Get a file's size in index tars.

    :param repo_id: The identifier of the repository.
    :type repo_id: str
    :param archive_in_repo: The path to the archive file in the repository.
    :type archive_in_repo: str
    :param file_in_archive: The path to the file inside the archive.
    :type file_in_archive: str
    :param repo_type: The type of the Hugging Face repository.
    :type repo_type: RepoTypeTyping, optional
    :param revision: The revision of the repository.
    :type revision: str, optional
    :param idx_repo_id: The identifier of the index repository.
    :type idx_repo_id: str, optional
    :param idx_file_in_repo: The path to the index file in the index repository.
    :type idx_file_in_repo: str, optional
    :param idx_repo_type: The type of the index repository.
    :type idx_repo_type: RepoTypeTyping, optional
    :param idx_revision: The revision of the index repository.
    :type idx_revision: str, optional
    :param hf_token: The Hugging Face access token.
    :type hf_token: str, optional
    :return: Return an integer which represents the size of this file.
    :rtype: int
    :raises FileNotFoundError: Raise this when file not exist in tar archive.

    Examples::
        >>> from hfutils.index import hf_tar_file_size
        >>>
        >>> hf_tar_file_size(
        ...     repo_id='deepghs/danbooru_newest',
        ...     archive_in_repo='images/0000.tar',
        ...     file_in_archive='7506000.jpg',
        ... )
        435671

    .. note::

        Besides, if the tar and index files are in different repositories, you can also use this function to
        get the file size by explicitly assigning the ``idx_repo_id`` argument.

        >>> from hfutils.index import hf_tar_file_size
        >>>
        >>> hf_tar_file_size(
        ...     repo_id='nyanko7/danbooru2023',
        ...     idx_repo_id='deepghs/danbooru2023_index',
        ...     archive_in_repo='original/data-0000.tar',
        ...     file_in_archive='1000.png'
        ... )
        11966
    """
    return hf_tar_file_info(
        repo_id=repo_id,
        archive_in_repo=archive_in_repo,
        file_in_archive=file_in_archive,
        repo_type=repo_type,
        revision=revision,
        idx_repo_id=idx_repo_id,
        idx_file_in_repo=idx_file_in_repo,
        idx_repo_type=idx_repo_type,
        idx_revision=idx_revision,
        hf_token=hf_token
    )['size']


class _WriteSHA256ValidatorProxyIO(BinaryProxyIO):
    """
    A proxy IO class that calculates SHA256 hash while writing data to the underlying stream.

    This class extends BinaryProxyIO to add SHA256 hash calculation functionality during write operations.
    The calculated hash can be accessed after closing the stream.

    :param stream: The binary stream to write to
    :type stream: BinaryIO
    :param need_validate: Whether SHA256 hash calculation is needed, defaults to True
    :type need_validate: bool
    """

    def __init__(self, stream: BinaryIO, need_validate: bool = True):
        super().__init__(stream)
        self._file_sha = sha256() if need_validate else None
        self._sha256 = None

    @property
    def sha256(self) -> Optional[str]:
        """
        Get the calculated SHA256 hash of the written data.

        :return: The hexadecimal representation of the SHA256 hash, or None if validation was disabled
        :rtype: Optional[str]
        """
        return self._sha256

    def _on_write(self, __s):
        """
        Update the SHA256 hash with the written data.

        :param __s: The bytes being written
        :type __s: bytes
        """
        if __s and self._file_sha is not None:
            self._file_sha.update(__s)

    def _after_close(self):
        """
        Finalize the SHA256 hash calculation after the stream is closed.
        """
        if self._file_sha is not None:
            self._sha256 = self._file_sha.hexdigest()


def _hf_tar_file_info_write(repo_id: str, archive_in_repo: str, file_in_archive: str, info: dict,
                            file_to_write: BinaryIO, repo_type: RepoTypeTyping = 'dataset', revision: str = 'main',
                            proxies: Optional[Dict] = None, user_agent: Union[Dict, str, None] = None,
                            headers: Optional[Dict[str, str]] = None, endpoint: Optional[str] = None,
                            silent: bool = False, hf_token: Optional[str] = None, no_validate: bool = False):
    """
    Extract a specific file from an archive in a Hugging Face repository and write it to a file-like object.

    This function downloads only the necessary portion of an archive file that contains the target file,
    extracts it, and writes it to the provided file object. It also validates the SHA256 hash of the
    extracted file if validation is enabled.

    :param repo_id: The repository ID where the archive is located
    :type repo_id: str
    :param archive_in_repo: The path to the archive file within the repository
    :type archive_in_repo: str
    :param file_in_archive: The path to the target file within the archive
    :type file_in_archive: str
    :param info: Dictionary containing metadata about the file (offset, size, and optionally sha256)
    :type info: dict
    :param file_to_write: The binary file-like object to write the extracted content to
    :type file_to_write: BinaryIO
    :param repo_type: The repository type, defaults to 'dataset'
    :type repo_type: RepoTypeTyping, optional
    :param revision: The repository revision, defaults to 'main'
    :type revision: str, optional
    :param proxies: Proxy configuration for HTTP requests, defaults to None
    :type proxies: Optional[Dict], optional
    :param user_agent: User agent information for HTTP requests, defaults to None
    :type user_agent: Union[Dict, str, None], optional
    :param headers: Additional HTTP headers for requests, defaults to None
    :type headers: Optional[Dict[str, str]], optional
    :param endpoint: The API endpoint to use, defaults to None
    :type endpoint: Optional[str], optional
    :param silent: Whether to suppress download progress display, defaults to False
    :type silent: bool, optional
    :param hf_token: Hugging Face authentication token, defaults to None
    :type hf_token: Optional[str], optional
    :param no_validate: Whether to skip SHA256 hash validation, defaults to False
    :type no_validate: bool, optional

    :raises ArchiveStandaloneFileIncompleteDownload: If the downloaded file size doesn't match the expected size
    :raises ArchiveStandaloneFileHashNotMatch: If the SHA256 hash of the downloaded file doesn't match the expected hash
    """
    url_to_download = hf_hub_url(repo_id, archive_in_repo, repo_type=repo_type, revision=revision, endpoint=endpoint)
    headers = build_hf_headers(
        token=hf_token,
        library_name=None,
        library_version=None,
        user_agent=user_agent,
        headers=headers,
    )
    start_bytes = info['offset']
    end_bytes = info['offset'] + info['size'] - 1
    headers['Range'] = f'bytes={start_bytes}-{end_bytes}'

    proxy = _WriteSHA256ValidatorProxyIO(file_to_write, need_validate=not no_validate)
    try:
        with tqdm(disable=True) as empty_tqdm:
            if info['size'] > 0:
                http_get(
                    url_to_download,
                    proxy,
                    proxies=proxies,
                    resume_size=0,
                    headers=headers,
                    expected_size=info['size'],
                    displayed_filename=file_in_archive,
                    _tqdm_bar=empty_tqdm if silent else None,
                )

        if proxy.tell() != info['size']:
            raise ArchiveStandaloneFileIncompleteDownload(
                f'Expected size is {size_to_bytes_str(info["size"], sigfigs=4, system="si")}, '
                f'but actually {size_to_bytes_str(proxy.tell(), sigfigs=4, system="si")} downloaded.'
            )

        proxy.close()
        if info.get('sha256') and not no_validate:
            if proxy.sha256 != info['sha256']:
                raise ArchiveStandaloneFileHashNotMatch(
                    f'Expected hash is {info["sha256"]!r}, but actually {proxy.sha256!r} found.'
                )

    finally:
        proxy.close()


def _check_hf_transfer_conflict():
    if constants.HF_HUB_ENABLE_HF_TRANSFER and vpip('huggingface_hub') < '0.31':
        warnings.warn(f"You are trying to use huggingface_hub=={huggingface_hub.__version__} "
                      f"with hf_transfer enabled at the same time, this may cause unexpected error "
                      f"(see: https://github.com/huggingface/huggingface_hub/issues/2978 for more details). "
                      f"We strongly recommend you to upgrade huggingface_hub to 0.31.0 or higher version, "
                      f"or simply disable the hf_transfer.")


def hf_tar_file_write_bytes(repo_id: str, archive_in_repo: str, file_in_archive: str, bin_file: BinaryIO,
                            repo_type: RepoTypeTyping = 'dataset', revision: str = 'main',
                            idx_repo_id: Optional[str] = None, idx_file_in_repo: Optional[str] = None,
                            idx_repo_type: Optional[RepoTypeTyping] = None, idx_revision: Optional[str] = None,
                            proxies: Optional[Dict] = None, user_agent: Union[Dict, str, None] = None,
                            headers: Optional[Dict[str, str]] = None, endpoint: Optional[str] = None,
                            silent: bool = False, hf_token: Optional[str] = None, no_cache: bool = False):
    """
    Extract a file from a tar archive in a Hugging Face repository and write it to a binary file-like object.

    This function retrieves a specific file from a tar archive stored in a Hugging Face repository
    and writes its content to the provided binary file-like object. It uses the index information
    to efficiently download only the necessary portion of the archive.

    :param repo_id: The identifier of the repository containing the tar archive.
    :type repo_id: str
    :param archive_in_repo: The path to the tar archive file within the repository.
    :type archive_in_repo: str
    :param file_in_archive: The path to the desired file inside the tar archive.
    :type file_in_archive: str
    :param bin_file: The binary file-like object to write the extracted content to.
    :type bin_file: BinaryIO
    :param repo_type: The type of the Hugging Face repository.
    :type repo_type: RepoTypeTyping, optional
    :param revision: The revision of the repository.
    :type revision: str, optional
    :param idx_repo_id: The identifier of the index repository if different from the main repository.
    :type idx_repo_id: Optional[str], optional
    :param idx_file_in_repo: The path to the index file in the index repository.
    :type idx_file_in_repo: Optional[str], optional
    :param idx_repo_type: The type of the index repository.
    :type idx_repo_type: Optional[RepoTypeTyping], optional
    :param idx_revision: The revision of the index repository.
    :type idx_revision: Optional[str], optional
    :param proxies: Proxy settings for the HTTP request.
    :type proxies: Optional[Dict], optional
    :param user_agent: Custom user agent for the HTTP request.
    :type user_agent: Union[Dict, str, None], optional
    :param headers: Additional headers for the HTTP request.
    :type headers: Optional[Dict[str, str]], optional
    :param endpoint: Custom Hugging Face API endpoint.
    :type endpoint: Optional[str], optional
    :param silent: Whether to suppress progress bar output.
    :type silent: bool, optional
    :param hf_token: Hugging Face authentication token.
    :type hf_token: Optional[str], optional
    :param no_cache: Whether to bypass the cache and force a new index file reading.
    :type no_cache: bool, optional

    :raises FileNotFoundError: If the specified file is not found in the tar archive.
    :raises ArchiveStandaloneFileIncompleteDownload: If the download is incomplete.
    :raises ArchiveStandaloneFileHashNotMatch: If the downloaded file's hash doesn't match the expected hash.

    Example::
        >>> import io
        >>> buffer = io.BytesIO()
        >>> hf_tar_file_write_bytes(
        ...     repo_id='deepghs/danbooru_newest',
        ...     archive_in_repo='images/0000.tar',
        ...     file_in_archive='7506000.jpg',
        ...     bin_file=buffer
        ... )
        >>> # Now buffer contains the file content
        >>> image_data = buffer.getvalue()

    .. warning::

        This function will probably get conflict with `hf_transfer`,
        so please make sure to upgrade to `huggingface_hub>=0.31` or
        disable the `hf_transfer` when running this function.
    """
    _check_hf_transfer_conflict()
    files = _hf_tar_get_processed_files(
        repo_id=repo_id,
        archive_in_repo=archive_in_repo,
        repo_type=repo_type,
        revision=revision,

        idx_repo_id=idx_repo_id,
        idx_file_in_repo=idx_file_in_repo,
        idx_repo_type=idx_repo_type,
        idx_revision=idx_revision,

        hf_token=hf_token,
        no_cache=no_cache,
    )
    if _n_path(file_in_archive) not in files:
        raise FileNotFoundError(f'File {file_in_archive!r} not found '
                                f'in {repo_type}s/{repo_id}@{revision}/{archive_in_repo}.')

    info = files[_n_path(file_in_archive)]
    _hf_tar_file_info_write(
        repo_id=repo_id,
        repo_type=repo_type,
        archive_in_repo=archive_in_repo,
        file_in_archive=file_in_archive,
        info=info,
        file_to_write=bin_file,
        revision=revision,

        proxies=proxies,
        user_agent=user_agent,
        endpoint=endpoint,
        headers=headers,
        silent=silent,
        hf_token=hf_token,
        no_validate=False,
    )


def hf_tar_file_download(repo_id: str, archive_in_repo: str, file_in_archive: str, local_file: str,
                         repo_type: RepoTypeTyping = 'dataset', revision: str = 'main',
                         idx_repo_id: Optional[str] = None, idx_file_in_repo: Optional[str] = None,
                         idx_repo_type: Optional[RepoTypeTyping] = None, idx_revision: Optional[str] = None,
                         proxies: Optional[Dict] = None, user_agent: Union[Dict, str, None] = None,
                         headers: Optional[Dict[str, str]] = None, endpoint: Optional[str] = None,
                         force_download: bool = False, silent: bool = False,
                         hf_token: Optional[str] = None, no_cache: bool = False):
    """
    Download a specific file from a tar archive stored in a Hugging Face repository.

    This function allows you to extract and download a single file from a tar archive
    that is hosted in a Hugging Face repository. It handles authentication, supports
    different repository types, and can work with separate index repositories.

    :param repo_id: The identifier of the repository containing the tar archive.
    :type repo_id: str
    :param archive_in_repo: The path to the tar archive file within the repository.
    :type archive_in_repo: str
    :param file_in_archive: The path to the desired file inside the tar archive.
    :type file_in_archive: str
    :param local_file: The local path where the downloaded file will be saved.
    :type local_file: str
    :param repo_type: The type of the Hugging Face repository (e.g., 'dataset', 'model', 'space').
    :type repo_type: RepoTypeTyping, optional
    :param revision: The specific revision of the repository to use.
    :type revision: str, optional
    :param idx_repo_id: The identifier of a separate index repository, if applicable.
    :type idx_repo_id: str, optional
    :param idx_file_in_repo: The path to the index file in the index repository.
    :type idx_file_in_repo: str, optional
    :param idx_repo_type: The type of the index repository.
    :type idx_repo_type: RepoTypeTyping, optional
    :param idx_revision: The revision of the index repository.
    :type idx_revision: str, optional
    :param proxies: Proxy settings for the HTTP request.
    :type proxies: Dict, optional
    :param user_agent: Custom user agent for the HTTP request.
    :type user_agent: Union[Dict, str, None], optional
    :param headers: Additional headers for the HTTP request.
    :type headers: Dict[str, str], optional
    :param endpoint: Custom Hugging Face API endpoint.
    :type endpoint: str, optional
    :param force_download: If True, force re-download even if the file exists locally.
    :type force_download: bool
    :param silent: If True, suppress progress bar output.
    :type silent: bool
    :param hf_token: Hugging Face authentication token.
    :type hf_token: str, optional
    :param no_cache: Whether to bypass the cache and force a new index file reading.
    :type no_cache: bool

    :raises FileNotFoundError: If the specified file is not found in the tar archive.
    :raises ArchiveStandaloneFileIncompleteDownload: If the download is incomplete.
    :raises ArchiveStandaloneFileHashNotMatch: If the downloaded file's hash doesn't match the expected hash.

    This function performs several steps:

    1. Retrieves the index of the tar archive.
    2. Checks if the desired file exists in the archive.
    3. Constructs the download URL and headers.
    4. Checks if the file already exists locally and matches the expected size and hash.
    5. Downloads the file if necessary, using byte range requests for efficiency.
    6. Verifies the downloaded file's size and hash.

    Usage examples:
        1. Basic usage:
            >>> hf_tar_file_download(
            ...     repo_id='deepghs/danbooru_newest',
            ...     archive_in_repo='images/0000.tar',
            ...     file_in_archive='7506000.jpg',
            ...     local_file='test_example.jpg'  # download destination
            ... )

        2. Using a separate index repository:
            >>> hf_tar_file_download(
            ...     repo_id='nyanko7/danbooru2023',
            ...     idx_repo_id='deepghs/danbooru2023_index',
            ...     archive_in_repo='original/data-0000.tar',
            ...     file_in_archive='1000.png',
            ...     local_file='test_example.png'  # download destination
            ... )

    .. note::

        - This function is particularly useful for efficiently downloading single files from large tar archives
          without having to download the entire archive.
        - It supports authentication via the `hf_token` parameter, which is crucial for accessing private repositories.
        - The function includes checks to avoid unnecessary downloads and to ensure the integrity of the downloaded file.

    .. warning::

        This function will probably get conflict with `hf_transfer`,
        so please make sure to upgrade to `huggingface_hub>=0.31` or
        disable the `hf_transfer` when running this function.
    """
    _check_hf_transfer_conflict()
    files = _hf_tar_get_processed_files(
        repo_id=repo_id,
        archive_in_repo=archive_in_repo,
        repo_type=repo_type,
        revision=revision,

        idx_repo_id=idx_repo_id,
        idx_file_in_repo=idx_file_in_repo,
        idx_repo_type=idx_repo_type,
        idx_revision=idx_revision,

        hf_token=hf_token,
        no_cache=no_cache,
    )
    if _n_path(file_in_archive) not in files:
        raise FileNotFoundError(f'File {file_in_archive!r} not found '
                                f'in {repo_type}s/{repo_id}@{revision}/{archive_in_repo}.')

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
        with open(local_file, 'wb') as f:
            _hf_tar_file_info_write(
                repo_id=repo_id,
                repo_type=repo_type,
                archive_in_repo=archive_in_repo,
                file_in_archive=file_in_archive,
                info=info,
                file_to_write=f,
                revision=revision,

                proxies=proxies,
                user_agent=user_agent,
                endpoint=endpoint,
                headers=headers,
                silent=silent,
                hf_token=hf_token,
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


def hf_tar_cache_reset(maxsize: Optional[int] = None):
    """
    Reset the tar archive index caches and optionally resize them.

    :param maxsize: New maximum size for the caches. If None, only clears the caches without resizing.
    :type maxsize: Optional[int]

    This function performs two operations:

    1. Clears both the index cache and processed files cache
    2. If maxsize is provided, recreates the caches with the new size

    Example::
        >>> hf_tar_cache_reset()  # Clear caches
        >>> hf_tar_cache_reset(maxsize=256)  # Clear and resize caches
    """
    global _HF_TAR_IDX_CACHE, _HF_TAR_IDX_PFILES_CACHE
    _HF_TAR_IDX_CACHE.clear()
    _HF_TAR_IDX_PFILES_CACHE.clear()
    if maxsize is not None and _HF_TAR_IDX_CACHE.maxsize != maxsize:
        _HF_TAR_IDX_CACHE = LRUCache(maxsize=maxsize)
        _HF_TAR_IDX_PFILES_CACHE = LRUCache(maxsize=maxsize)

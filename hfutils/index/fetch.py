import json
import os.path
import threading
from collections import defaultdict
from typing import Optional, Dict, Union, List

from huggingface_hub.file_download import http_get, hf_hub_url
from huggingface_hub.utils import build_hf_headers
from tqdm import tqdm

from .hash import _f_sha256
from ..operate.base import RepoTypeTyping, get_hf_client


class ArchiveStandaloneFileIncompleteDownload(Exception):
    """
    Exception raised when a standalone file in an archive is incompletely downloaded.
    """


class ArchiveStandaloneFileHashNotMatch(Exception):
    """
    Exception raised when the hash of a standalone file in an archive does not match.
    """


_HF_TAR_IDX_LOCKS = defaultdict(threading.Lock)


def hf_tar_get_index(repo_id: str, archive_in_repo: str,
                     repo_type: RepoTypeTyping = 'dataset', revision: str = 'main',
                     idx_repo_id: Optional[str] = None, idx_file_in_repo: Optional[str] = None,
                     idx_repo_type: Optional[RepoTypeTyping] = None, idx_revision: Optional[str] = None,
                     hf_token: Optional[str] = None):
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
    body, _ = os.path.splitext(archive_in_repo)
    default_index_file = f'{body}.json'
    f_repo_id = idx_repo_id or repo_id
    f_repo_type = idx_repo_type or repo_type
    f_filename = idx_file_in_repo or default_index_file
    f_revision = idx_revision or revision
    with _HF_TAR_IDX_LOCKS[(f_repo_id, f_repo_type, f_filename, f_revision)]:
        with open(hf_client.hf_hub_download(
                repo_id=f_repo_id,
                repo_type=f_repo_type,
                filename=f_filename,
                revision=f_revision,
        ), 'r') as f:
            return json.load(f)


def hf_tar_list_files(repo_id: str, archive_in_repo: str,
                      repo_type: RepoTypeTyping = 'dataset', revision: str = 'main',
                      idx_repo_id: Optional[str] = None, idx_file_in_repo: Optional[str] = None,
                      idx_repo_type: Optional[RepoTypeTyping] = None, idx_revision: Optional[str] = None,
                      hf_token: Optional[str] = None) -> List[str]:
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
    )

    return list(index_data['files'].keys())


def hf_tar_file_exists(repo_id: str, archive_in_repo: str, file_in_archive: str,
                       repo_type: RepoTypeTyping = 'dataset', revision: str = 'main',
                       idx_repo_id: Optional[str] = None, idx_file_in_repo: Optional[str] = None,
                       idx_repo_type: Optional[RepoTypeTyping] = None, idx_revision: Optional[str] = None,
                       hf_token: Optional[str] = None):
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
    )
    files = _hf_files_process(index['files'])
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
                     hf_token: Optional[str] = None) -> dict:
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
    )
    files = _hf_files_process(index['files'])
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


def hf_tar_file_download(repo_id: str, archive_in_repo: str, file_in_archive: str, local_file: str,
                         repo_type: RepoTypeTyping = 'dataset', revision: str = 'main',
                         idx_repo_id: Optional[str] = None, idx_file_in_repo: Optional[str] = None,
                         idx_repo_type: Optional[RepoTypeTyping] = None, idx_revision: Optional[str] = None,
                         proxies: Optional[Dict] = None, user_agent: Union[Dict, str, None] = None,
                         headers: Optional[Dict[str, str]] = None, endpoint: Optional[str] = None,
                         force_download: bool = False, silent: bool = False, hf_token: Optional[str] = None):
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
    """
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
    )
    files = _hf_files_process(index['files'])
    if _n_path(file_in_archive) not in files:
        raise FileNotFoundError(f'File {file_in_archive!r} not found '
                                f'in {repo_type}s/{repo_id}@{revision}/{archive_in_repo}.')

    info = files[_n_path(file_in_archive)]

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

    if not force_download and os.path.exists(local_file) and \
            os.path.isfile(local_file) and os.path.getsize(local_file) == info['size']:
        _expected_sha256 = info.get('sha256')
        if not _expected_sha256 or _f_sha256(local_file) == _expected_sha256:
            # file already ready, no need to download it again
            return

    if os.path.dirname(local_file):
        os.makedirs(os.path.dirname(local_file), exist_ok=True)
    try:
        with open(local_file, 'wb') as f, tqdm(disable=True) as empty_tqdm:
            if info['size'] > 0:
                http_get(
                    url_to_download,
                    f,
                    proxies=proxies,
                    resume_size=0,
                    headers=headers,
                    expected_size=info['size'],
                    displayed_filename=file_in_archive,
                    _tqdm_bar=empty_tqdm if silent else None,
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

import json
import os.path
from typing import Optional, Dict, Union

from huggingface_hub.file_download import http_get, hf_hub_url
from huggingface_hub.utils import build_hf_headers

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
    """
    hf_client = get_hf_client(hf_token)
    body, _ = os.path.splitext(archive_in_repo)
    default_index_file = f'{body}.json'
    with open(hf_client.hf_hub_download(
            repo_id=idx_repo_id or repo_id,
            repo_type=idx_repo_type or repo_type,
            filename=idx_file_in_repo or default_index_file,
            revision=idx_revision or revision,
    ), 'r') as f:
        return json.load(f)


def hf_tar_list_files(repo_id: str, archive_in_repo: str,
                      repo_type: RepoTypeTyping = 'dataset', revision: str = 'main',
                      idx_repo_id: Optional[str] = None, idx_file_in_repo: Optional[str] = None,
                      idx_repo_type: Optional[RepoTypeTyping] = None, idx_revision: Optional[str] = None,
                      hf_token: Optional[str] = None):
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


def hf_tar_file_download(repo_id: str, archive_in_repo: str, file_in_archive: str, local_file: str,
                         repo_type: RepoTypeTyping = 'dataset', revision: str = 'main',
                         idx_repo_id: Optional[str] = None, idx_file_in_repo: Optional[str] = None,
                         idx_repo_type: Optional[RepoTypeTyping] = None, idx_revision: Optional[str] = None,
                         proxies: Optional[Dict] = None, user_agent: Union[Dict, str, None] = None,
                         headers: Optional[Dict[str, str]] = None, endpoint: Optional[str] = None,
                         hf_token: Optional[str] = None):
    """
    Download a file from a tar archive file in a Hugging Face repository.

    :param repo_id: The identifier of the repository.
    :type repo_id: str
    :param archive_in_repo: The path to the archive file in the repository.
    :type archive_in_repo: str
    :param file_in_archive: The path to the file inside the archive.
    :type file_in_archive: str
    :param local_file: The path to save the downloaded file locally.
    :type local_file: str
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
    :param proxies: The proxies to be used for the HTTP request.
    :type proxies: Dict, optional
    :param user_agent: The user agent for the HTTP request.
    :type user_agent: Union[Dict, str, None], optional
    :param headers: The additional headers for the HTTP request.
    :type headers: Dict[str, str], optional
    :param endpoint: The Hugging Face API endpoint.
    :type endpoint: str, optional
    :param hf_token: The Hugging Face access token.
    :type hf_token: str, optional
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

    if os.path.dirname(local_file):
        os.makedirs(os.path.dirname(local_file), exist_ok=True)
    try:
        with open(local_file, 'wb') as f:
            if info['size'] > 0:
                http_get(
                    url_to_download,
                    f,
                    proxies=proxies,
                    resume_size=0,
                    headers=headers,
                    expected_size=info['size'],
                    displayed_filename=file_in_archive,
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

import json
import os.path
from typing import Optional, Dict, Union

from huggingface_hub.file_download import http_get, hf_hub_url
from huggingface_hub.utils import build_hf_headers

from .hash import _f_sha256
from ..operate.base import RepoTypeTyping, get_hf_client


class ArchiveStandaloneFileIncompleteDownload(Exception):
    pass


class ArchiveStandaloneFileHashNotMatch(Exception):
    pass


def hf_tar_get_index(repo_id: str, archive_in_repo: str,
                     repo_type: RepoTypeTyping = 'dataset', revision: str = 'main',
                     idx_repo_id: Optional[str] = None, idx_file_in_repo: Optional[str] = None,
                     idx_repo_type: Optional[RepoTypeTyping] = None, idx_revision: Optional[str] = None,
                     hf_token: Optional[str] = None):
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
    return os.path.normpath(os.path.join('/', path))


def _hf_files_process(files: Dict[str, dict]):
    return {_n_path(key): value for key, value in files.items()}


def hf_tar_file_download(repo_id: str, archive_in_repo: str, file_in_archive: str, local_file: str,
                         repo_type: RepoTypeTyping = 'dataset', revision: str = 'main',
                         idx_repo_id: Optional[str] = None, idx_file_in_repo: Optional[str] = None,
                         idx_repo_type: Optional[RepoTypeTyping] = None, idx_revision: Optional[str] = None,
                         proxies: Optional[Dict] = None, user_agent: Union[Dict, str, None] = None,
                         headers: Optional[Dict[str, str]] = None, endpoint: Optional[str] = None,
                         hf_token: Optional[str] = None):
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

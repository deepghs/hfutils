import os.path
from concurrent.futures import ThreadPoolExecutor
from typing import List

from hbutils.system import TemporaryDirectory
from huggingface_hub import hf_hub_url

from .base import RepoTypeTyping, _get_hf_token, list_files_in_repository, _IGNORE_PATTERN_UNSET
from ..archive import archive_unpack
from ..utils import download_file, tqdm


def download_file_to_file(local_file: str, repo_id: str, file_in_repo: str,
                          repo_type: RepoTypeTyping = 'dataset', revision: str = 'main', silent: bool = False):
    headers = {}
    token = _get_hf_token()
    if token:
        headers['Authorization'] = f'Bearer {token}'

    parent_dir = os.path.dirname(local_file)
    if parent_dir:
        os.makedirs(parent_dir, exist_ok=True)
    download_file(hf_hub_url(
        repo_id=repo_id,
        repo_type=repo_type,
        filename=file_in_repo,
        revision=revision,
    ), local_file, headers=headers, silent=silent)


def download_archive_as_directory(local_directory: str, repo_id: str, file_in_repo: str,
                                  repo_type: RepoTypeTyping = 'dataset', revision: str = 'main', silent: bool = False):
    with TemporaryDirectory() as td:
        archive_file = os.path.join(td, os.path.basename(file_in_repo))
        download_file_to_file(archive_file, repo_id, file_in_repo, repo_type, revision, silent=silent)
        archive_unpack(archive_file, local_directory, silent=silent)


def download_directory_as_directory(local_directory: str, repo_id: str, dir_in_repo: str = '.',
                                    repo_type: RepoTypeTyping = 'dataset', revision: str = 'main',
                                    silent: bool = False, ignore_patterns: List[str] = _IGNORE_PATTERN_UNSET):
    files = list_files_in_repository(repo_id, repo_type, dir_in_repo, revision, ignore_patterns)
    progress = tqdm(files, silent=silent, desc=f'Downloading {dir_in_repo!r} ...')

    def _download_one_file(rel_file):
        download_file_to_file(
            local_file=os.path.join(local_directory, rel_file),
            repo_id=repo_id,
            file_in_repo=f'{dir_in_repo}/{rel_file}',
            repo_type=repo_type,
            revision=revision,
            silent=silent
        )
        progress.update()

    tp = ThreadPoolExecutor()
    for file in files:
        tp.submit(_download_one_file, file)
    tp.shutdown(wait=True)

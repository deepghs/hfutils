import logging
import os.path
import shutil
from concurrent.futures import ThreadPoolExecutor
from typing import List, Optional

import requests.exceptions

from .base import RepoTypeTyping, list_files_in_repository, _IGNORE_PATTERN_UNSET, get_hf_client
from .validate import is_local_file_ready
from ..archive import archive_unpack
from ..utils import tqdm, TemporaryDirectory, hf_normpath


def download_file_to_file(local_file: str, repo_id: str, file_in_repo: str,
                          repo_type: RepoTypeTyping = 'dataset', revision: str = 'main',
                          resume_download: bool = True, hf_token: Optional[str] = None):
    """
    Download a file from a Hugging Face repository and save it to a local file.

    :param local_file: The local file path to save the downloaded file.
    :type local_file: str
    :param repo_id: The identifier of the repository.
    :type repo_id: str
    :param file_in_repo: The file path within the repository.
    :type file_in_repo: str
    :param repo_type: The type of the repository ('dataset', 'model', 'space').
    :type repo_type: RepoTypeTyping
    :param revision: The revision of the repository (e.g., branch, tag, commit hash).
    :type revision: str
    :param resume_download: Resume the existing download.
    :type resume_download: bool
    :param hf_token: Huggingface token for API client, use ``HF_TOKEN`` variable if not assigned.
    :type hf_token: str, optional
    """
    hf_client = get_hf_client(hf_token)
    relative_filename = os.path.join(*file_in_repo.split("/"))
    with TemporaryDirectory() as td:
        temp_path = os.path.join(td, relative_filename)
        try:
            hf_client.hf_hub_download(
                repo_id=repo_id,
                repo_type=repo_type,
                filename=hf_normpath(file_in_repo),
                revision=revision,
                local_dir=td,
                resume_download=resume_download,
            )
        finally:
            if os.path.exists(temp_path):
                if os.path.dirname(local_file):
                    os.makedirs(os.path.dirname(local_file), exist_ok=True)
                shutil.move(temp_path, local_file)


def download_archive_as_directory(local_directory: str, repo_id: str, file_in_repo: str,
                                  repo_type: RepoTypeTyping = 'dataset', revision: str = 'main',
                                  password: Optional[str] = None, hf_token: Optional[str] = None):
    """
    Download an archive file from a Hugging Face repository and extract it to a local directory.

    :param local_directory: The local directory path to extract the downloaded archive.
    :type local_directory: str
    :param repo_id: The identifier of the repository.
    :type repo_id: str
    :param file_in_repo: The file path within the repository.
    :type file_in_repo: str
    :param repo_type: The type of the repository ('dataset', 'model', 'space').
    :type repo_type: RepoTypeTyping
    :param revision: The revision of the repository (e.g., branch, tag, commit hash).
    :type revision: str
    :param password: The password of the archive file.
    :type password: str, optional
    :param hf_token: Huggingface token for API client, use ``HF_TOKEN`` variable if not assigned.
    :type hf_token: str, optional
    """
    with TemporaryDirectory() as td:
        archive_file = os.path.join(td, os.path.basename(file_in_repo))
        download_file_to_file(archive_file, repo_id, file_in_repo, repo_type, revision, hf_token=hf_token)
        archive_unpack(archive_file, local_directory, password=password)


def download_directory_as_directory(
        local_directory: str, repo_id: str, dir_in_repo: str = '.', pattern: str = '**/*',
        repo_type: RepoTypeTyping = 'dataset', revision: str = 'main',
        silent: bool = False, ignore_patterns: List[str] = _IGNORE_PATTERN_UNSET,
        resume_download: bool = True, max_workers: int = 8, max_retries: int = 5,
        hf_token: Optional[str] = None
):
    """
    Download all files in a directory from a Hugging Face repository to a local directory.

    :param local_directory: The local directory path to save the downloaded files.
    :type local_directory: str
    :param repo_id: The identifier of the repository.
    :type repo_id: str
    :param dir_in_repo: The directory path within the repository.
    :type dir_in_repo: str
    :param pattern: Patterns for filtering.
    :type pattern: str
    :param repo_type: The type of the repository ('dataset', 'model', 'space').
    :type repo_type: RepoTypeTyping
    :param revision: The revision of the repository (e.g., branch, tag, commit hash).
    :type revision: str
    :param silent: If True, suppress progress bar output.
    :type silent: bool
    :param ignore_patterns: List of file patterns to ignore.
    :type ignore_patterns: List[str]
    :param max_workers: Max workers when downloading. Default is ``8``.
    :type max_workers: int
    :param max_retries: Max retry times when downloading. Default is ``5``.
    :type max_retries: int
    :param resume_download: Resume the existing download.
    :type resume_download: bool
    :param hf_token: Huggingface token for API client, use ``HF_TOKEN`` variable if not assigned.
    :type hf_token: str, optional
    """
    files = list_files_in_repository(
        repo_id=repo_id,
        repo_type=repo_type,
        subdir=dir_in_repo,
        pattern=pattern,
        revision=revision,
        ignore_patterns=ignore_patterns,
        hf_token=hf_token,
    )
    progress = tqdm(files, silent=silent, desc=f'Downloading {dir_in_repo!r} ...')

    def _download_one_file(rel_file):
        current_resume_download = resume_download
        try:
            dst_file = os.path.join(local_directory, rel_file)
            file_in_repo = hf_normpath(f'{dir_in_repo}/{rel_file}')
            if os.path.exists(dst_file) and is_local_file_ready(
                    repo_id=repo_id,
                    repo_type=repo_type,
                    local_file=dst_file,
                    file_in_repo=file_in_repo,
                    revision=revision,
                    hf_token=hf_token,
            ):
                logging.info(f'Local file {rel_file} is ready, download skipped.')
            else:
                tries = 0
                while True:
                    try:
                        download_file_to_file(
                            local_file=dst_file,
                            repo_id=repo_id,
                            file_in_repo=file_in_repo,
                            repo_type=repo_type,
                            revision=revision,
                            resume_download=current_resume_download,
                            hf_token=hf_token,
                        )
                    except requests.exceptions.RequestException as err:
                        if tries < max_retries:
                            tries += 1
                            logging.warning(f'Download {rel_file!r} failed, retry ({tries}/{max_retries}) - {err!r}.')
                            current_resume_download = True
                        else:
                            raise
                    else:
                        break

            progress.update()
        except Exception as err:
            logging.error(f'Unexpected error when downloading {rel_file!r} - {err!r}')

    tp = ThreadPoolExecutor(max_workers=max_workers)
    for file in files:
        tp.submit(_download_one_file, file)
    tp.shutdown(wait=True)

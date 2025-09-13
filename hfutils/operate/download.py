"""
This module provides functions for downloading files and directories from Hugging Face repositories.

It includes utilities for downloading individual files, archives, and entire directories,
with support for concurrent downloads, retries, and progress tracking.

The module interacts with the Hugging Face Hub API to fetch repository contents and
download files, handling various repository types and revisions.

Key features:

- Download individual files from Hugging Face repositories
- Download and extract archive files
- Download entire directories with pattern matching and ignore rules
- Concurrent downloads with configurable worker count
- Retry mechanism for failed downloads
- Progress tracking with tqdm
- Support for different repository types (dataset, model, space)
- Token-based authentication for accessing private repositories

This module is particularly useful for managing and synchronizing local copies of
Hugging Face repository contents, especially when dealing with large datasets or models.
"""

import logging
import os.path
import shutil
from concurrent.futures import ThreadPoolExecutor
from typing import Optional, Union, List

import requests.exceptions
from huggingface_hub.hf_api import RepoFile

from .base import RepoTypeTyping, get_hf_client, \
    list_repo_files_in_repository
from .validate import is_local_file_ready, _raw_check_local_file
from ..archive import archive_unpack
from ..utils import tqdm, TemporaryDirectory, hf_normpath


def _raw_download_file(td: str, local_file: str, repo_id: str, file_in_repo: str,
                       repo_type: RepoTypeTyping = 'dataset', revision: str = 'main',
                       hf_token: Optional[str] = None):
    """
    Download a file from a Hugging Face repository to a temporary directory and then move it to the final location.

    This internal function handles the actual download process using the Hugging Face Hub client.
    It downloads the file to a temporary location first and then moves it to the final destination
    to ensure atomic file operations and prevent partial downloads from corrupting the target file.

    :param td: Temporary directory path where the file will be initially downloaded.
    :type td: str
    :param local_file: The final local file path where the downloaded file will be moved.
    :type local_file: str
    :param repo_id: The identifier of the repository (e.g., 'username/repo-name').
    :type repo_id: str
    :param file_in_repo: The file path within the repository relative to the repository root.
    :type file_in_repo: str
    :param repo_type: The type of the repository ('dataset', 'model', 'space').
    :type repo_type: RepoTypeTyping
    :param revision: The revision of the repository (e.g., branch name, tag, commit hash).
    :type revision: str
    :param hf_token: Hugging Face authentication token for accessing private repositories.
    :type hf_token: str, optional

    Example::
        >>> import tempfile
        >>> with tempfile.TemporaryDirectory() as td:
        ...     _raw_download_file(
        ...         td=td,
        ...         local_file="/path/to/local/file.txt",
        ...         repo_id="username/dataset",
        ...         file_in_repo="data/file.txt",
        ...         repo_type="dataset"
        ...     )
    """
    hf_client = get_hf_client(hf_token=hf_token)
    relative_filename = os.path.join(*file_in_repo.split("/"))
    temp_path = os.path.join(td, relative_filename)
    try:
        hf_client.hf_hub_download(
            repo_id=repo_id,
            repo_type=repo_type,
            filename=hf_normpath(file_in_repo),
            revision=revision,
            local_dir=td,
        )
    finally:
        if os.path.exists(temp_path):
            if os.path.dirname(local_file):
                os.makedirs(os.path.dirname(local_file), exist_ok=True)
            shutil.move(temp_path, local_file)


def download_file_to_file(local_file: str, repo_id: str, file_in_repo: str,
                          repo_type: RepoTypeTyping = 'dataset', revision: str = 'main',
                          soft_mode_when_check: bool = False, hf_token: Optional[str] = None):
    """
    Download a file from a Hugging Face repository and save it to a local file.

    This function downloads a single file from a Hugging Face repository to a specified local path.
    It includes validation to check if the local file already exists and is up-to-date, skipping
    the download if the file is already present and valid.

    :param local_file: The local file path where the downloaded file will be saved.
    :type local_file: str
    :param repo_id: The identifier of the repository (e.g., 'username/repo-name').
    :type repo_id: str
    :param file_in_repo: The file path within the repository relative to the repository root.
    :type file_in_repo: str
    :param repo_type: The type of the repository ('dataset', 'model', 'space').
    :type repo_type: RepoTypeTyping
    :param revision: The revision of the repository (e.g., branch name, tag, commit hash).
    :type revision: str
    :param soft_mode_when_check: If True, only check the file size for validation instead of full integrity check.
    :type soft_mode_when_check: bool
    :param hf_token: Hugging Face authentication token for accessing private repositories.
    :type hf_token: str, optional

    Example::
        >>> download_file_to_file(
        ...     local_file="./local_model.bin",
        ...     repo_id="username/my-model",
        ...     file_in_repo="pytorch_model.bin",
        ...     repo_type="model"
        ... )
    """
    with TemporaryDirectory() as td:
        if os.path.exists(local_file) and is_local_file_ready(
                repo_id=repo_id,
                repo_type=repo_type,
                local_file=local_file,
                file_in_repo=file_in_repo,
                revision=revision,
                hf_token=hf_token,
                soft_mode=soft_mode_when_check,
        ):
            logging.info(f'Local file {local_file!r} is ready, download skipped.')
        else:
            _raw_download_file(
                td=td,
                local_file=local_file,
                repo_id=repo_id,
                file_in_repo=file_in_repo,
                repo_type=repo_type,
                revision=revision,
                hf_token=hf_token,
            )


def download_archive_as_directory(local_directory: str, repo_id: str, file_in_repo: str,
                                  repo_type: RepoTypeTyping = 'dataset', revision: str = 'main',
                                  password: Optional[str] = None, hf_token: Optional[str] = None):
    """
    Download an archive file from a Hugging Face repository and extract it to a local directory.

    This function downloads an archive file (such as ZIP, TAR, etc.) from a Hugging Face repository
    and automatically extracts its contents to the specified local directory. It supports password-protected
    archives and handles the extraction process transparently.

    :param local_directory: The local directory path where the archive contents will be extracted.
    :type local_directory: str
    :param repo_id: The identifier of the repository (e.g., 'username/repo-name').
    :type repo_id: str
    :param file_in_repo: The archive file path within the repository relative to the repository root.
    :type file_in_repo: str
    :param repo_type: The type of the repository ('dataset', 'model', 'space').
    :type repo_type: RepoTypeTyping
    :param revision: The revision of the repository (e.g., branch name, tag, commit hash).
    :type revision: str
    :param password: The password for extracting password-protected archives.
    :type password: str, optional
    :param hf_token: Hugging Face authentication token for accessing private repositories.
    :type hf_token: str, optional

    Example::
        >>> download_archive_as_directory(
        ...     local_directory="./extracted_data",
        ...     repo_id="username/dataset",
        ...     file_in_repo="data.zip",
        ...     repo_type="dataset"
        ... )
    """
    with TemporaryDirectory() as td:
        archive_file = os.path.join(td, os.path.basename(file_in_repo))
        download_file_to_file(archive_file, repo_id, file_in_repo, repo_type, revision, hf_token=hf_token)
        archive_unpack(archive_file, local_directory, password=password)


def download_directory_as_directory(
        local_directory: str, repo_id: str, dir_in_repo: str = '.', pattern: Union[List[str], str] = '**/*',
        repo_type: RepoTypeTyping = 'dataset', revision: str = 'main', silent: bool = False,
        max_workers: int = 8, max_retries: int = 5,
        soft_mode_when_check: bool = False, hf_token: Optional[str] = None
):
    """
    Download all files in a directory from a Hugging Face repository to a local directory.

    This function recursively downloads all files from a specified directory in a Hugging Face repository
    to a local directory. It supports concurrent downloads with configurable worker threads, retry mechanisms
    for failed downloads, and pattern-based file filtering. The function maintains the directory structure
    from the repository in the local destination.

    :param local_directory: The local directory path where downloaded files will be saved.
    :type local_directory: str
    :param repo_id: The identifier of the repository (e.g., 'username/repo-name').
    :type repo_id: str
    :param dir_in_repo: The directory path within the repository to download. Use '.' for repository root.
    :type dir_in_repo: str
    :param pattern: File patterns for filtering which files to download. Can be a single pattern string or list of patterns.
    :type pattern: Union[List[str], str]
    :param repo_type: The type of the repository ('dataset', 'model', 'space').
    :type repo_type: RepoTypeTyping
    :param revision: The revision of the repository (e.g., branch name, tag, commit hash).
    :type revision: str
    :param silent: If True, suppress progress bar output during download.
    :type silent: bool
    :param max_workers: Maximum number of concurrent download threads.
    :type max_workers: int
    :param max_retries: Maximum number of retry attempts for failed downloads.
    :type max_retries: int
    :param soft_mode_when_check: If True, only check file size for validation instead of full integrity check.
    :type soft_mode_when_check: bool
    :param hf_token: Hugging Face authentication token for accessing private repositories.
    :type hf_token: str, optional

    Example::
        >>> download_directory_as_directory(
        ...     local_directory="./local_dataset",
        ...     repo_id="username/my-dataset",
        ...     dir_in_repo="data",
        ...     pattern="*.json",
        ...     repo_type="dataset",
        ...     max_workers=4
        ... )
    """
    files = list_repo_files_in_repository(
        repo_id=repo_id,
        repo_type=repo_type,
        subdir=dir_in_repo,
        pattern=pattern,
        revision=revision,
        hf_token=hf_token,
    )
    progress = tqdm(files, silent=silent, desc=f'Downloading {dir_in_repo!r} ...')

    def _download_one_file(repo_file: RepoFile, rel_file: str):
        """
        Download a single file with retry mechanism and progress tracking.

        :param repo_file: The repository file metadata object.
        :type repo_file: RepoFile
        :param rel_file: The relative file path within the directory.
        :type rel_file: str
        """
        with TemporaryDirectory() as td:
            try:
                dst_file = os.path.join(local_directory, rel_file)
                file_in_repo = hf_normpath(f'{dir_in_repo}/{rel_file}')
                if os.path.exists(dst_file) and _raw_check_local_file(
                        repo_file=repo_file,
                        local_file=dst_file,
                        soft_mode=soft_mode_when_check,
                ):
                    logging.info(f'Local file {rel_file} is ready, download skipped.')
                else:
                    tries = 0
                    while True:
                        try:
                            _raw_download_file(
                                td=td,
                                local_file=dst_file,
                                repo_id=repo_id,
                                file_in_repo=file_in_repo,
                                repo_type=repo_type,
                                revision=revision,
                                hf_token=hf_token,
                            )
                        except requests.exceptions.RequestException as err:
                            if tries < max_retries:
                                tries += 1
                                logging.warning(
                                    f'Download {rel_file!r} failed, retry ({tries}/{max_retries}) - {err!r}.')
                            else:
                                raise
                        else:
                            break

                progress.update()
            except Exception as err:
                logging.exception(f'Unexpected error when downloading {rel_file!r} - {err!r}')
                raise

    tp = ThreadPoolExecutor(max_workers=max_workers)
    for item, file in files:
        tp.submit(_download_one_file, item, file)
    tp.shutdown(wait=True)

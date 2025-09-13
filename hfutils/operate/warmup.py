"""
Huggingface File Management Module

This module provides utilities for managing and downloading files from Huggingface repositories.
It includes functions for warming up (pre-downloading) individual files and entire directories
from Huggingface repositories, with support for concurrent downloads, retries, and progress tracking.
"""
import logging
from concurrent.futures import ThreadPoolExecutor
from typing import Optional, Union, List

import requests
from huggingface_hub import hf_hub_download
from huggingface_hub.hf_api import RepoFile
from tqdm import tqdm

from .base import RepoTypeTyping, list_repo_files_in_repository
from ..utils import hf_normpath


def hf_warmup_file(repo_id: str, filename: str, repo_type: RepoTypeTyping = 'dataset', revision: str = 'main',
                   hf_token: Optional[str] = None, cache_dir: Optional[str] = None):
    """
    Download and cache a single file from Huggingface repository.

    This function downloads a specific file from a Huggingface repository and caches it locally.
    It's useful for pre-downloading files that will be accessed later, ensuring they're available
    in the local cache for faster subsequent access.

    :param repo_id: ID of the huggingface repository (e.g., 'username/repository')
    :type repo_id: str
    :param filename: Name of the file to download including path within repository
    :type filename: str
    :param repo_type: Type of repository ('dataset', 'model', etc.), defaults to 'dataset'
    :type repo_type: RepoTypeTyping
    :param revision: Git revision to use, defaults to 'main'
    :type revision: str
    :param hf_token: Huggingface authentication token for private repositories
    :type hf_token: Optional[str]
    :param cache_dir: Directory to cache the downloaded file, if None uses default cache
    :type cache_dir: Optional[str]

    :return: Local path to the downloaded file
    :rtype: str

    Example::
        >>> # Download a model configuration file
        >>> local_path = hf_warmup_file('bert-base-uncased', 'config.json', repo_type='model')
        >>> # Download a dataset file with specific revision
        >>> local_path = hf_warmup_file('username/dataset', 'data/train.csv', revision='v1.0')
    """
    return hf_hub_download(
        repo_id=repo_id,
        repo_type=repo_type,
        filename=filename,
        revision=revision,
        token=hf_token,
        cache_dir=cache_dir,
    )


def hf_warmup_directory(repo_id: str, dir_in_repo: str = '.', pattern: Union[List[str], str] = '**/*',
                        repo_type: RepoTypeTyping = 'dataset', revision: str = 'main', silent: bool = False,
                        max_workers: int = 8, max_retries: int = 5, hf_token: Optional[str] = None,
                        cache_dir: Optional[str] = None):
    """
    Download and cache an entire directory from Huggingface repository with concurrent processing.

    This function efficiently downloads multiple files from a directory in a Huggingface repository
    using concurrent workers. It includes retry mechanisms for failed downloads and progress tracking.
    This is particularly useful for pre-downloading large datasets or model repositories.

    :param repo_id: ID of the huggingface repository (e.g., 'username/repository')
    :type repo_id: str
    :param dir_in_repo: Directory path within the repository to download, defaults to '.' (root)
    :type dir_in_repo: str
    :param pattern: Glob pattern for filtering files (e.g., '*.txt' for text files only), defaults to '**/*'
    :type pattern: Union[List[str], str]
    :param repo_type: Type of repository ('dataset', 'model', etc.), defaults to 'dataset'
    :type repo_type: RepoTypeTyping
    :param revision: Git revision to use, defaults to 'main'
    :type revision: str
    :param silent: Whether to hide progress bar, defaults to False
    :type silent: bool
    :param max_workers: Maximum number of concurrent download workers, defaults to 8
    :type max_workers: int
    :param max_retries: Maximum number of retry attempts for failed downloads, defaults to 5
    :type max_retries: int
    :param hf_token: Huggingface authentication token for private repositories
    :type hf_token: Optional[str]
    :param cache_dir: Directory to cache the downloaded files
    :type cache_dir: Optional[str]

    Example::
        >>> # Download all files from the root directory
        >>> hf_warmup_directory('username/dataset')
        >>> # Download only .txt files from the 'data' directory using 4 workers
        >>> hf_warmup_directory('username/repo', 'data', '*.txt', max_workers=4)
        >>> # Download with custom retry settings and silent mode
        >>> hf_warmup_directory('username/repo', 'models', max_retries=3, silent=True)
    """
    files = list_repo_files_in_repository(
        repo_id=repo_id,
        repo_type=repo_type,
        subdir=dir_in_repo,
        pattern=pattern,
        revision=revision,
        hf_token=hf_token,
    )
    progress = tqdm(files, disable=silent, desc=f'Downloading {dir_in_repo!r} ...')

    def _warmup_one_file(repo_file: RepoFile, rel_file: str):
        """
        Internal helper function to download a single file with retry mechanism.

        This function handles the download of individual files with automatic retry logic
        for handling transient network errors. It updates the progress bar upon successful
        completion and logs any errors encountered during the process.

        :param repo_file: Repository file object containing file metadata
        :type repo_file: RepoFile
        :param rel_file: Relative path of the file within the directory
        :type rel_file: str
        """
        _ = repo_file
        try:
            file_in_repo = hf_normpath(f'{dir_in_repo}/{rel_file}')
            tries = 0
            while True:
                try:
                    hf_hub_download(
                        repo_id=repo_id,
                        repo_type=repo_type,
                        filename=file_in_repo,
                        revision=revision,
                        token=hf_token,
                        cache_dir=cache_dir,
                    )
                except requests.exceptions.RequestException as err:
                    if tries < max_retries:
                        tries += 1
                        logging.warning(f'Download {rel_file!r} failed, retry ({tries}/{max_retries}) - {err!r}.')
                    else:
                        raise
                else:
                    break
            progress.update()
        except Exception as err:
            logging.exception(f'Unexpected error when downloading {rel_file!r} - {err!r}')

    tp = ThreadPoolExecutor(max_workers=max_workers)
    for item, file in files:
        tp.submit(_warmup_one_file, item, file)
    tp.shutdown(wait=True)

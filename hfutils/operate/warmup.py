"""
Huggingface File Management Module

This module provides utilities for managing and downloading files from Huggingface repositories.
It includes functions for warming up (pre-downloading) individual files and entire directories
from Huggingface repositories, with support for concurrent downloads, retries, and progress tracking.
"""
import logging
from concurrent.futures import ThreadPoolExecutor
from typing import Optional, List

import requests
from huggingface_hub import hf_hub_download
from huggingface_hub.hf_api import RepoFile
from tqdm import tqdm

from .base import RepoTypeTyping, list_repo_files_in_repository
from .download import _IGNORE_PATTERN_UNSET
from ..utils import hf_normpath


def hf_warmup_file(repo_id: str, filename: str, repo_type: RepoTypeTyping = 'dataset', revision: str = 'main',
                   hf_token: Optional[str] = None, cache_dir: Optional[str] = None):
    """
    Download and cache a single file from Huggingface repository.

    :param repo_id: ID of the huggingface repository (e.g., 'username/repository')
    :type repo_id: str
    :param filename: Name of the file to download including path within repository
    :type filename: str
    :param repo_type: Type of repository ('dataset', 'model', etc.)
    :type repo_type: RepoTypeTyping
    :param revision: Git revision to use, defaults to 'main'
    :type revision: str
    :param hf_token: Huggingface authentication token for private repositories
    :type hf_token: Optional[str]
    :param cache_dir: Directory to cache the downloaded file, if None uses default cache
    :type cache_dir: Optional[str]

    :return: Local path to the downloaded file
    :rtype: str

    Example:
        >>> local_path = hf_warmup_file('bert-base-uncased', 'config.json', repo_type='model')
    """
    return hf_hub_download(
        repo_id=repo_id,
        repo_type=repo_type,
        filename=filename,
        revision=revision,
        token=hf_token,
        cache_dir=cache_dir,
    )


def hf_warmup_directory(repo_id: str, dir_in_repo: str = '.', pattern: str = '**/*',
                        repo_type: RepoTypeTyping = 'dataset', revision: str = 'main',
                        silent: bool = False, ignore_patterns: List[str] = _IGNORE_PATTERN_UNSET,
                        max_workers: int = 8, max_retries: int = 5, hf_token: Optional[str] = None,
                        cache_dir: Optional[str] = None):
    """
    Download and cache an entire directory from Huggingface repository with concurrent processing.

    :param repo_id: ID of the huggingface repository (e.g., 'username/repository')
    :type repo_id: str
    :param dir_in_repo: Directory path within the repository to download
    :type dir_in_repo: str
    :param pattern: Glob pattern for filtering files (e.g., '*.txt' for text files only)
    :type pattern: str
    :param repo_type: Type of repository ('dataset', 'model', etc.)
    :type repo_type: RepoTypeTyping
    :param revision: Git revision to use
    :type revision: str
    :param silent: Whether to hide progress bar
    :type silent: bool
    :param ignore_patterns: List of patterns to ignore during download
    :type ignore_patterns: List[str]
    :param max_workers: Maximum number of concurrent download workers
    :type max_workers: int
    :param max_retries: Maximum number of retry attempts for failed downloads
    :type max_retries: int
    :param hf_token: Huggingface authentication token for private repositories
    :type hf_token: Optional[str]
    :param cache_dir: Directory to cache the downloaded files
    :type cache_dir: Optional[str]

    Example:
        >>> # Downloads all .txt files from the 'data' directory using 4 workers
        >>> hf_warmup_directory('username/repo', 'data', '*.txt', max_workers=4)
    """
    files = list_repo_files_in_repository(
        repo_id=repo_id,
        repo_type=repo_type,
        subdir=dir_in_repo,
        pattern=pattern,
        revision=revision,
        ignore_patterns=ignore_patterns,
        hf_token=hf_token,
    )
    progress = tqdm(files, disable=silent, desc=f'Downloading {dir_in_repo!r} ...')

    def _warmup_one_file(repo_file: RepoFile, rel_file: str):
        """
        Internal helper function to download a single file with retry mechanism.

        :param repo_file: Repository file object
        :type repo_file: RepoFile
        :param rel_file: Relative path of the file
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

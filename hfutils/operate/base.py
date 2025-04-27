"""
This module provides utilities for interacting with the Hugging Face Hub API and filesystem.
It includes functions for retrieving API clients, listing files in repositories, and handling
file patterns and ignore rules.

The module offers the following main functionalities:

1. Retrieving Hugging Face API tokens and clients
2. Accessing the Hugging Face filesystem
3. Listing files in Hugging Face repositories with pattern matching and ignore rules
4. Parsing and normalizing Hugging Face filesystem paths

These utilities are designed to simplify working with Hugging Face repositories, especially
when dealing with datasets, models, and spaces.
"""

import fnmatch
import logging
import os
import re
from functools import lru_cache
from typing import Literal, List, Optional, Union, Iterator, Tuple

from huggingface_hub import HfApi, HfFileSystem
from huggingface_hub.hf_api import RepoFolder, RepoFile
from huggingface_hub.utils import HfHubHTTPError

from ..utils import parse_hf_fs_path, hf_fs_path, tqdm, hf_normpath

RepoTypeTyping = Literal['dataset', 'model', 'space']
REPO_TYPES = ['dataset', 'model', 'space']


@lru_cache()
def _get_hf_token() -> Optional[str]:
    """
    Retrieve the Hugging Face token from the environment variable.

    This function checks for the 'HF_TOKEN' environment variable and returns its value.
    It is cached to avoid repeated environment variable lookups.

    :return: The Hugging Face token if set, otherwise None.
    :rtype: Optional[str]
    """
    return os.environ.get('HF_TOKEN')


@lru_cache()
def get_hf_client(hf_token: Optional[str] = None) -> HfApi:
    """
    Get the Hugging Face API client.

    This function returns an instance of the Hugging Face API client. If a token is not provided,
    it attempts to use the token from the environment variable.

    :param hf_token: Hugging Face token for API client. If not provided, uses the 'HF_TOKEN' environment variable.
    :type hf_token: Optional[str]

    :return: An instance of the Hugging Face API client.
    :rtype: HfApi

    :example:

        >>> client = get_hf_client()
        >>> # Use client to interact with Hugging Face API
        >>> client.list_repos(organization="huggingface")
    """
    return HfApi(token=hf_token or _get_hf_token())


@lru_cache()
def get_hf_fs(hf_token: Optional[str] = None) -> HfFileSystem:
    """
    Get the Hugging Face file system.

    This function returns an instance of the Hugging Face file system. If a token is not provided,
    it attempts to use the token from the environment variable. The file system is configured
    not to use listings cache to ensure fresh results.

    :param hf_token: Hugging Face token for API client. If not provided, uses the 'HF_TOKEN' environment variable.
    :type hf_token: Optional[str]

    :return: An instance of the Hugging Face file system.
    :rtype: HfFileSystem

    :example:

        >>> fs = get_hf_fs()
        >>> # Use fs to interact with Hugging Face file system
        >>> fs.ls("dataset/example")
    """
    # use_listings_cache=False is necessary
    # or the result of glob and ls will be cached, the unittest will down
    return HfFileSystem(token=hf_token or _get_hf_token(), use_listings_cache=False)


_DEFAULT_IGNORE_PATTERNS = ['.git*']
_IGNORE_PATTERN_UNSET = object()


def _is_file_ignored(file_segments: List[str], ignore_patterns: List[str]) -> bool:
    """
    Check if a file should be ignored based on the given ignore patterns.

    This function checks each segment of the file path against the provided ignore patterns.
    If any segment matches any of the patterns, the file is considered ignored.

    :param file_segments: The segments of the file path.
    :type file_segments: List[str]
    :param ignore_patterns: List of file patterns to ignore.
    :type ignore_patterns: List[str]

    :return: True if the file should be ignored, False otherwise.
    :rtype: bool

    :example:

        >>> _is_file_ignored(['folder', 'file.txt'], ['.git*', '*.log'])
        False
        >>> _is_file_ignored(['folder', '.gitignore'], ['.git*', '*.log'])
        True
    """
    for segment in file_segments:
        for pattern in ignore_patterns:
            if fnmatch.fnmatch(segment, pattern):
                return True

    return False


def list_all_with_pattern(
        repo_id: str, pattern: str = '**/*', repo_type: RepoTypeTyping = 'dataset',
        revision: str = 'main', startup_batch: int = 500, batch_factor: float = 0.8,
        hf_token: Optional[str] = None, silent: bool = False
) -> Iterator[Union[RepoFile, RepoFolder]]:
    """
    List all files and folders in a Hugging Face repository matching a given pattern.

    This function retrieves information about files and folders in a repository that match
    the specified pattern. It uses batching to handle large repositories efficiently.

    :param repo_id: The identifier of the repository.
    :type repo_id: str
    :param pattern: Wildcard pattern to match files and folders. Default is `**/*` (all files and folders).
    :type pattern: str
    :param repo_type: The type of the repository ('dataset', 'model', 'space'). Default is 'dataset'.
    :type repo_type: RepoTypeTyping
    :param revision: The revision of the repository (e.g., branch, tag, commit hash). Default is 'main'.
    :type revision: str
    :param startup_batch: Initial batch size for retrieving path information. Default is 500.
    :type startup_batch: int
    :param batch_factor: Factor to reduce batch size if a request fails. Default is 0.8.
    :type batch_factor: float
    :param hf_token: Hugging Face token for API client. If not provided, uses the 'HF_TOKEN' environment variable.
    :type hf_token: Optional[str]
    :param silent: If True, suppresses progress bar. Default is False.
    :type silent: bool

    :return: An iterator of RepoFile and RepoFolder objects matching the pattern.
    :rtype: Iterator[Union[RepoFile, RepoFolder]]

    :raises HfHubHTTPError: If there's an error in the API request that's not related to batch size.

    :example:

        >>> for item in list_all_with_pattern("username/repo", pattern="*.txt"):
        ...     print(item.path)
    """
    hf_fs = get_hf_fs(hf_token=hf_token)
    hf_client = get_hf_client(hf_token=hf_token)

    try:
        raw_paths = hf_fs.glob(hf_fs_path(
            repo_id=repo_id,
            repo_type=repo_type,
            filename=pattern,
            revision=revision,
        ))
    except FileNotFoundError:
        return
    paths = [parse_hf_fs_path(path).filename for path in raw_paths]

    offset, batch_size = 0, startup_batch
    progress = tqdm(total=len(paths), desc='Paths Info', silent=silent)
    while offset < len(paths):
        batch_paths = paths[offset:offset + batch_size]
        try:
            all_items = hf_client.get_paths_info(
                repo_id=repo_id,
                repo_type=repo_type,
                paths=batch_paths,
                revision=revision,
            )
        except HfHubHTTPError as err:
            if err.response.status_code == 413:
                new_batch_size = max(1, int(round(batch_size * batch_factor)))
                logging.warning(f'Reducing batch size {batch_size} --> {new_batch_size} ...')
                batch_size = new_batch_size
                continue
            raise
        else:
            progress.update(len(all_items))
            offset += len(all_items)
            yield from all_items


def list_repo_files_in_repository(
        repo_id: str, repo_type: RepoTypeTyping = 'dataset',
        subdir: str = '', pattern: str = '**/*', revision: str = 'main',
        ignore_patterns: List[str] = _IGNORE_PATTERN_UNSET,
        hf_token: Optional[str] = None, silent: bool = False) -> List[Tuple[RepoFile, str]]:
    """
    List repository files with their paths in a Hugging Face repository.

    This function returns a list of tuples containing RepoFile objects and their corresponding paths
    that match the given pattern and are not ignored by the ignored patterns.

    :param repo_id: The identifier of the repository.
    :type repo_id: str
    :param repo_type: The type of the repository ('dataset', 'model', 'space'). Default is 'dataset'.
    :type repo_type: RepoTypeTyping
    :param subdir: The subdirectory to list files from. Default is an empty string (root directory).
    :type subdir: str
    :param pattern: Wildcard pattern of the target files. Default is `**/*` (all files).
    :type pattern: str
    :param revision: The revision of the repository (e.g., branch, tag, commit hash). Default is 'main'.
    :type revision: str
    :param ignore_patterns: List of file patterns to ignore. If not set, uses default ignore patterns.
    :type ignore_patterns: List[str]
    :param hf_token: Hugging Face token for API client. If not provided, uses the 'HF_TOKEN' environment variable.
    :type hf_token: Optional[str]
    :param silent: If True, suppresses progress bar. Default is False.
    :type silent: bool

    :return: A list of tuples containing RepoFile objects and their corresponding paths.
    :rtype: List[Tuple[RepoFile, str]]

    :example:

        >>> files = list_repo_files_in_repository("username/repo", pattern="*.txt")
        >>> for repo_file, path in files:
        ...     print(f"File: {path}, Size: {repo_file.size}")
    """
    if ignore_patterns is _IGNORE_PATTERN_UNSET:
        ignore_patterns = _DEFAULT_IGNORE_PATTERNS

    if subdir and subdir != '.':
        pattern = f'{subdir}/{pattern}'

    result = []
    for item in list_all_with_pattern(
            repo_id=repo_id,
            repo_type=repo_type,
            revision=revision,
            pattern=pattern,
            hf_token=hf_token,
            silent=silent,
    ):
        if isinstance(item, RepoFile):
            path = hf_normpath(os.path.relpath(item.path, start=subdir or '.'))
            segments = list(filter(bool, re.split(r'[\\/]+', path)))
            if not _is_file_ignored(segments, ignore_patterns):
                result.append((item, path))

    return result


def list_files_in_repository(
        repo_id: str, repo_type: RepoTypeTyping = 'dataset',
        subdir: str = '', pattern: str = '**/*', revision: str = 'main',
        ignore_patterns: List[str] = _IGNORE_PATTERN_UNSET,
        hf_token: Optional[str] = None, silent: bool = False) -> List[str]:
    """
    List files in a Hugging Face repository based on the given parameters.

    This function retrieves a list of file paths in a specified repository that match
    the given pattern and are not ignored by the ignored patterns.

    :param repo_id: The identifier of the repository.
    :type repo_id: str
    :param repo_type: The type of the repository ('dataset', 'model', 'space'). Default is 'dataset'.
    :type repo_type: RepoTypeTyping
    :param subdir: The subdirectory to list files from. Default is an empty string (root directory).
    :type subdir: str
    :param pattern: Wildcard pattern of the target files. Default is `**/*` (all files).
    :type pattern: str
    :param revision: The revision of the repository (e.g., branch, tag, commit hash). Default is 'main'.
    :type revision: str
    :param ignore_patterns: List of file patterns to ignore. If not set, uses default ignore patterns.
    :type ignore_patterns: List[str]
    :param hf_token: Hugging Face token for API client. If not provided, uses the 'HF_TOKEN' environment variable.
    :type hf_token: Optional[str]
    :param silent: If True, suppresses progress bar. Default is False.
    :type silent: bool

    :return: A list of file paths that match the criteria.
    :rtype: List[str]

    :example:

        >>> files = list_files_in_repository("username/repo", pattern="*.txt", ignore_patterns=[".git*", "*.log"])
        >>> print(files)
        ['file1.txt', 'folder/file2.txt']
    """
    return [
        path for _, path in list_repo_files_in_repository(
            repo_id=repo_id,
            repo_type=repo_type,
            subdir=subdir,
            pattern=pattern,
            revision=revision,
            ignore_patterns=ignore_patterns,
            hf_token=hf_token,
            silent=silent,
        )
    ]

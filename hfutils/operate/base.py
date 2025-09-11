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

import os
from functools import lru_cache
from typing import Literal, List, Optional, Union, Tuple

import wcmatch.fnmatch as fnmatch
from huggingface_hub import HfApi, HfFileSystem
from huggingface_hub.hf_api import RepoFolder, RepoFile

from ..utils import hf_normpath

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


def _fn_path_pattern_norm(pattern: Union[List[str], str]) -> Union[List[str], str]:
    if isinstance(pattern, (list, tuple)):
        return [hf_normpath(p) for p in pattern]
    else:
        return hf_normpath(pattern)


def _fn_path_pattern_subdir_single(pattern: str, subdir: str) -> str:
    if pattern.startswith('!'):
        pattern = f'!{subdir}/{pattern[1:]}'
    else:
        pattern = f'{subdir}/{pattern}'
    pattern = hf_normpath(pattern)
    return pattern


def _fn_path_pattern_subdir(pattern: Union[List[str], str], subdir: str) -> Union[List[str], str]:
    if isinstance(pattern, (list, tuple)):
        return [_fn_path_pattern_subdir_single(p, subdir) for p in pattern]
    else:
        return _fn_path_pattern_subdir_single(pattern, subdir)


def hf_repo_glob(
        repo_id: str, pattern: Union[List[str], str] = '*', repo_type: RepoTypeTyping = 'dataset',
        revision: str = 'main', include_files: bool = True, include_directories: bool = False,
        hf_token: Optional[str] = None,
) -> List[Union[RepoFile, RepoFolder]]:
    hf_client = get_hf_client(hf_token=hf_token)
    pattern = _fn_path_pattern_norm(pattern)

    items = []
    for item in hf_client.list_repo_tree(
            repo_id=repo_id,
            repo_type=repo_type,
            revision=revision,
            recursive=True,
    ):
        if (
                (include_files and isinstance(item, RepoFile)) or
                (include_directories and isinstance(item, RepoFolder))
        ) and fnmatch.fnmatch(
            filename=hf_normpath(item.rfilename),
            patterns=pattern,
            flags=(fnmatch.CASE | fnmatch.NEGATE | fnmatch.NEGATEALL | fnmatch.DOTMATCH),
        ):
            items.append(item)

    return items


def list_all_with_pattern(
        repo_id: str, pattern: Union[List[str], str] = '*', repo_type: RepoTypeTyping = 'dataset',
        revision: str = 'main', hf_token: Optional[str] = None
) -> List[Union[RepoFile, RepoFolder]]:
    """
    List all files and folders in a Hugging Face repository matching a given pattern.

    This function retrieves information about files and folders in a repository that match
    the specified pattern. It uses batching to handle large repositories efficiently.

    :param repo_id: The identifier of the repository.
    :type repo_id: str
    :param pattern: Wildcard pattern to match files and folders. Default is `*` (all files and folders).
    :type pattern: str
    :param repo_type: The type of the repository ('dataset', 'model', 'space'). Default is 'dataset'.
    :type repo_type: RepoTypeTyping
    :param revision: The revision of the repository (e.g., branch, tag, commit hash). Default is 'main'.
    :type revision: str
    :param hf_token: Hugging Face token for API client. If not provided, uses the 'HF_TOKEN' environment variable.
    :type hf_token: Optional[str]

    :return: An iterator of RepoFile and RepoFolder objects matching the pattern.
    :rtype: List[Union[RepoFile, RepoFolder]]

    :raises HfHubHTTPError: If there's an error in the API request that's not related to batch size.

    :example:

        >>> for item in list_all_with_pattern("username/repo", pattern="*.txt"):
        ...     print(item.path)
    """
    return hf_repo_glob(
        repo_id=repo_id,
        repo_type=repo_type,
        revision=revision,
        pattern=pattern,
        hf_token=hf_token,
        include_files=True,
        include_directories=True,
    )


_PATTERN_UNSET = object()
_DEFAULT_PATTERN_WITH_IGNORE = ['*', '!.git*']


def list_repo_files_in_repository(
        repo_id: str, repo_type: RepoTypeTyping = 'dataset',
        subdir: str = '', pattern: Union[List[str], str] = _PATTERN_UNSET, revision: str = 'main',
        hf_token: Optional[str] = None) -> List[Tuple[RepoFile, str]]:
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
    :param pattern: Wildcard pattern of the target files. Default is `*` (all files).
    :type pattern: str
    :param revision: The revision of the repository (e.g., branch, tag, commit hash). Default is 'main'.
    :type revision: str
    :param hf_token: Hugging Face token for API client. If not provided, uses the 'HF_TOKEN' environment variable.
    :type hf_token: Optional[str]

    :return: A list of tuples containing RepoFile objects and their corresponding paths.
    :rtype: List[Tuple[RepoFile, str]]

    :example:

        >>> files = list_repo_files_in_repository("username/repo", pattern="*.txt")
        >>> for repo_file, path in files:
        ...     print(f"File: {path}, Size: {repo_file.size}")
    """
    if pattern is _PATTERN_UNSET:
        pattern = _DEFAULT_PATTERN_WITH_IGNORE
    if subdir and subdir != '.':
        pattern = _fn_path_pattern_subdir(pattern, subdir)

    result = []
    for item in hf_repo_glob(
            repo_id=repo_id,
            repo_type=repo_type,
            revision=revision,
            pattern=pattern,
            include_files=True,
            include_directories=False,
            hf_token=hf_token,
    ):
        path = hf_normpath(os.path.relpath(item.path, start=subdir or '.'))
        result.append((item, path))

    return result


def list_files_in_repository(
        repo_id: str, repo_type: RepoTypeTyping = 'dataset',
        subdir: str = '', pattern: Union[List[str], str] = _PATTERN_UNSET, revision: str = 'main',
        hf_token: Optional[str] = None) -> List[str]:
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
    :param pattern: Wildcard pattern of the target files. Default is `*` (all files).
    :type pattern: str
    :param revision: The revision of the repository (e.g., branch, tag, commit hash). Default is 'main'.
    :type revision: str
    :param hf_token: Hugging Face token for API client. If not provided, uses the 'HF_TOKEN' environment variable.
    :type hf_token: Optional[str]

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
            hf_token=hf_token,
        )
    ]

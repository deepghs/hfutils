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

from huggingface_hub import HfApi, HfFileSystem
from huggingface_hub.errors import RepositoryNotFoundError, GatedRepoError, DisabledRepoError, RevisionNotFoundError
from huggingface_hub.hf_api import RepoFolder, RepoFile
from wcmatch import glob

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

    Example::

        >>> token = _get_hf_token()
        >>> print(token is not None)
        True  # if HF_TOKEN is set in environment
    """
    return os.environ.get('HF_TOKEN')


@lru_cache()
def get_hf_client(hf_token: Optional[str] = None) -> HfApi:
    """
    Get the Hugging Face API client.

    This function returns an instance of the Hugging Face API client. If a token is not provided,
    it attempts to use the token from the environment variable. The client is cached to avoid
    creating multiple instances with the same token.

    :param hf_token: Hugging Face token for API client. If not provided, uses the 'HF_TOKEN' environment variable.
    :type hf_token: Optional[str]

    :return: An instance of the Hugging Face API client.
    :rtype: HfApi

    Example::

        >>> client = get_hf_client()
        >>> # Use client to interact with Hugging Face API
        >>> models = client.list_models(limit=5)
    """
    return HfApi(token=hf_token or _get_hf_token() or None)


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

    Example::

        >>> fs = get_hf_fs()
        >>> # Use fs to interact with Hugging Face file system
        >>> files = fs.ls("datasets/squad")
    """
    # use_listings_cache=False is necessary
    # or the result of glob and ls will be cached, the unittest will down
    return HfFileSystem(token=hf_token or _get_hf_token() or None, use_listings_cache=False)


def _fn_path_pattern_norm(pattern: Union[List[str], str]) -> Union[List[str], str]:
    """
    Normalize file path patterns using the Hugging Face path normalization.

    This function takes a pattern or list of patterns and normalizes them using
    the hf_normpath function to ensure consistent path formatting.

    :param pattern: A single pattern string or list of pattern strings to normalize.
    :type pattern: Union[List[str], str]

    :return: Normalized pattern(s) in the same format as input.
    :rtype: Union[List[str], str]

    Example::

        >>> pattern = _fn_path_pattern_norm("./data//files/*.txt")
        >>> print(pattern)
        data/files/*.txt
    """
    if isinstance(pattern, (list, tuple)):
        return [hf_normpath(p) for p in pattern]
    else:
        return hf_normpath(pattern)


def _fn_path_pattern_subdir_single(pattern: str, subdir: str) -> str:
    """
    Adjust a single pattern to work within a subdirectory.

    This function modifies a pattern to be relative to a specific subdirectory.
    It handles negation patterns (starting with '!') appropriately by preserving
    the negation while prepending the subdirectory path.

    :param pattern: The pattern to adjust.
    :type pattern: str
    :param subdir: The subdirectory to prepend to the pattern.
    :type subdir: str

    :return: The adjusted pattern for the subdirectory.
    :rtype: str

    Example::

        >>> pattern = _fn_path_pattern_subdir_single("*.txt", "data")
        >>> print(pattern)
        data/*.txt
        >>> neg_pattern = _fn_path_pattern_subdir_single("!*.log", "logs")
        >>> print(neg_pattern)
        !logs/*.log
    """
    if pattern.startswith('!'):
        pattern = f'!{subdir}/{pattern[1:]}'
    else:
        pattern = f'{subdir}/{pattern}'
    pattern = hf_normpath(pattern)
    return pattern


def _fn_path_pattern_subdir(pattern: Union[List[str], str], subdir: str) -> Union[List[str], str]:
    """
    Adjust patterns to work within a subdirectory.

    This function modifies patterns to be relative to a specific subdirectory,
    handling both single patterns and lists of patterns. It preserves the input
    type and applies subdirectory adjustment to each pattern.

    :param pattern: The pattern(s) to adjust.
    :type pattern: Union[List[str], str]
    :param subdir: The subdirectory to prepend to the patterns.
    :type subdir: str

    :return: The adjusted pattern(s) for the subdirectory.
    :rtype: Union[List[str], str]

    Example::

        >>> patterns = _fn_path_pattern_subdir(["*.txt", "!*.log"], "data")
        >>> print(patterns)
        ['data/*.txt', '!data/*.log']
    """
    if isinstance(pattern, (list, tuple)):
        return [_fn_path_pattern_subdir_single(p, subdir) for p in pattern]
    else:
        return _fn_path_pattern_subdir_single(pattern, subdir)


def hf_repo_glob(
        repo_id: str, pattern: Union[List[str], str] = '**/*', repo_type: RepoTypeTyping = 'dataset',
        revision: str = 'main', include_files: bool = True, include_directories: bool = False,
        raise_when_base_not_exist: bool = False, return_path: bool = False, hf_token: Optional[str] = None,
) -> List[Union[RepoFile, RepoFolder, str]]:
    """
    Glob files and directories in a Hugging Face repository using pattern matching.

    This function performs pattern matching on files and directories in a Hugging Face
    repository, similar to filesystem globbing. It supports wildcard patterns and
    negation patterns for flexible file selection.

    .. note::
        Pattern matching syntax supports:

        - ``*``: Matches everything except slashes (single level)
        - ``**``: Matches zero or more directories recursively (requires GLOBSTAR flag, which is enabled)
        - ``?``: Matches any single character
        - ``[seq]``: Matches any character in sequence
        - ``[!seq]``: Matches any character not in sequence
        - ``!pattern``: Negation pattern when used at start (requires NEGATE flag, which is enabled)
        - Multiple patterns can be provided as a list
        - Negation patterns filter out matches from inclusion patterns
        - Dot files are matched by default (DOTMATCH flag is enabled)

        Note that `*` only matches at a single directory level, while `**/*` matches
        recursively including subdirectories and the top level.

    :param repo_id: The identifier of the repository.
    :type repo_id: str
    :param pattern: Wildcard pattern(s) to match files and folders. Default is '**/*' (all items).
    :type pattern: Union[List[str], str]
    :param repo_type: The type of the repository ('dataset', 'model', 'space'). Default is 'dataset'.
    :type repo_type: RepoTypeTyping
    :param revision: The revision of the repository (e.g., branch, tag, commit hash). Default is 'main'.
    :type revision: str
    :param include_files: Whether to include files in the results. Default is True.
    :type include_files: bool
    :param include_directories: Whether to include directories in the results. Default is False.
    :type include_directories: bool
    :param raise_when_base_not_exist: Whether to raise an exception when the repository doesn't exist. Default is False.
    :type raise_when_base_not_exist: bool
    :param return_path: Whether to return file paths as strings instead of RepoFile/RepoFolder objects. Default is False.
    :type return_path: bool
    :param hf_token: Hugging Face token for API client. If not provided, uses the 'HF_TOKEN' environment variable.
    :type hf_token: Optional[str]

    :return: A list of RepoFile and/or RepoFolder objects matching the pattern, or strings if return_path is True.
    :rtype: List[Union[RepoFile, RepoFolder, str]]

    :raises RepositoryNotFoundError: If the repository is not found and raise_when_base_not_exist is True.
    :raises GatedRepoError: If the repository is gated and raise_when_base_not_exist is True.
    :raises DisabledRepoError: If the repository is disabled and raise_when_base_not_exist is True.
    :raises RevisionNotFoundError: If the revision is not found and raise_when_base_not_exist is True.

    Example::

        >>> # Get all Python files in a repository
        >>> files = hf_repo_glob("username/repo", pattern="*.py")
        >>> # Get all files except hidden ones
        >>> files = hf_repo_glob("username/repo", pattern=["**/*", "!.*"])
        >>> # Get only directories
        >>> dirs = hf_repo_glob("username/repo", pattern="**/*", include_files=False, include_directories=True)
        >>> # Get paths as strings
        >>> paths = hf_repo_glob("username/repo", pattern="*.txt", return_path=True)
    """
    hf_client = get_hf_client(hf_token=hf_token)
    pattern = _fn_path_pattern_norm(pattern)

    items = []
    try:
        for item in hf_client.list_repo_tree(
                repo_id=repo_id,
                repo_type=repo_type,
                revision=revision,
                recursive=True,
        ):
            if (
                    (include_files and isinstance(item, RepoFile)) or
                    (include_directories and isinstance(item, RepoFolder))
            ) and glob.globmatch(
                filename=hf_normpath(item.path),
                patterns=pattern,
                flags=(glob.CASE | glob.NEGATE | glob.NEGATEALL | glob.DOTMATCH | glob.GLOBSTAR),
            ):
                if return_path:
                    items.append(hf_normpath(item.path))
                else:
                    items.append(item)
    except (RepositoryNotFoundError, GatedRepoError, DisabledRepoError, RevisionNotFoundError):
        if raise_when_base_not_exist:
            raise
        else:
            return []

    return items


def list_all_with_pattern(
        repo_id: str, pattern: Union[List[str], str] = '**/*', repo_type: RepoTypeTyping = 'dataset',
        revision: str = 'main', raise_when_base_not_exist: bool = False, hf_token: Optional[str] = None
) -> List[Union[RepoFile, RepoFolder]]:
    """
    List all files and folders in a Hugging Face repository matching a given pattern.

    This function retrieves information about files and folders in a repository that match
    the specified pattern. It includes both files and directories in the results by default.

    :param repo_id: The identifier of the repository.
    :type repo_id: str
    :param pattern: Wildcard pattern(s) to match files and folders. Default is '**/*' (all files and folders).
    :type pattern: Union[List[str], str]
    :param repo_type: The type of the repository ('dataset', 'model', 'space'). Default is 'dataset'.
    :type repo_type: RepoTypeTyping
    :param revision: The revision of the repository (e.g., branch, tag, commit hash). Default is 'main'.
    :type revision: str
    :param raise_when_base_not_exist: Whether to raise an exception when the repository doesn't exist. Default is False.
    :type raise_when_base_not_exist: bool
    :param hf_token: Hugging Face token for API client. If not provided, uses the 'HF_TOKEN' environment variable.
    :type hf_token: Optional[str]

    :return: A list of RepoFile and RepoFolder objects matching the pattern.
    :rtype: List[Union[RepoFile, RepoFolder]]

    Example::

        >>> # List all items matching a pattern
        >>> items = list_all_with_pattern("username/repo", pattern="*.txt")
        >>> for item in items:
        ...     print(f"{'File' if isinstance(item, RepoFile) else 'Folder'}: {item.path}")
    """
    return hf_repo_glob(
        repo_id=repo_id,
        repo_type=repo_type,
        revision=revision,
        pattern=pattern,
        hf_token=hf_token,
        include_files=True,
        include_directories=True,
        raise_when_base_not_exist=raise_when_base_not_exist,
    )


_PATTERN_UNSET = object()
_DEFAULT_PATTERN_WITH_IGNORE = ['**/*', '!.git*']


def list_repo_files_in_repository(
        repo_id: str, repo_type: RepoTypeTyping = 'dataset',
        subdir: str = '', pattern: Union[List[str], str] = _PATTERN_UNSET, revision: str = 'main',
        raise_when_base_not_exist: bool = False, hf_token: Optional[str] = None) -> List[Tuple[RepoFile, str]]:
    """
    List repository files with their paths in a Hugging Face repository.

    This function returns a list of tuples containing RepoFile objects and their corresponding
    relative paths that match the given pattern. By default, it excludes git-related files
    using the pattern ['**/*', '!.git*'].

    :param repo_id: The identifier of the repository.
    :type repo_id: str
    :param repo_type: The type of the repository ('dataset', 'model', 'space'). Default is 'dataset'.
    :type repo_type: RepoTypeTyping
    :param subdir: The subdirectory to list files from. Default is an empty string (root directory).
    :type subdir: str
    :param pattern: Wildcard pattern(s) of the target files. Default includes all files except git files.
    :type pattern: Union[List[str], str]
    :param revision: The revision of the repository (e.g., branch, tag, commit hash). Default is 'main'.
    :type revision: str
    :param raise_when_base_not_exist: Whether to raise an exception when the repository doesn't exist. Default is False.
    :type raise_when_base_not_exist: bool
    :param hf_token: Hugging Face token for API client. If not provided, uses the 'HF_TOKEN' environment variable.
    :type hf_token: Optional[str]

    :return: A list of tuples containing RepoFile objects and their corresponding relative paths.
    :rtype: List[Tuple[RepoFile, str]]

    Example::

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
            raise_when_base_not_exist=raise_when_base_not_exist,
            hf_token=hf_token,
    ):
        path = hf_normpath(os.path.relpath(item.path, start=subdir or '.'))
        result.append((item, path))

    return result


def list_files_in_repository(
        repo_id: str, repo_type: RepoTypeTyping = 'dataset',
        subdir: str = '', pattern: Union[List[str], str] = _PATTERN_UNSET, revision: str = 'main',
        raise_when_base_not_exist: bool = False, hf_token: Optional[str] = None) -> List[str]:
    """
    List files in a Hugging Face repository based on the given parameters.

    This function retrieves a list of file paths in a specified repository that match
    the given pattern. By default, it excludes git-related files and returns only
    the relative paths as strings.

    :param repo_id: The identifier of the repository.
    :type repo_id: str
    :param repo_type: The type of the repository ('dataset', 'model', 'space'). Default is 'dataset'.
    :type repo_type: RepoTypeTyping
    :param subdir: The subdirectory to list files from. Default is an empty string (root directory).
    :type subdir: str
    :param pattern: Wildcard pattern(s) of the target files. Default includes all files except git files.
    :type pattern: Union[List[str], str]
    :param revision: The revision of the repository (e.g., branch, tag, commit hash). Default is 'main'.
    :type revision: str
    :param raise_when_base_not_exist: Whether to raise an exception when the repository doesn't exist. Default is False.
    :type raise_when_base_not_exist: bool
    :param hf_token: Hugging Face token for API client. If not provided, uses the 'HF_TOKEN' environment variable.
    :type hf_token: Optional[str]

    :return: A list of file paths that match the criteria.
    :rtype: List[str]

    Example::

        >>> files = list_files_in_repository("username/repo", pattern="*.txt")
        >>> print(files)
        ['file1.txt', 'folder/file2.txt']
        >>> # List files in a specific subdirectory
        >>> files = list_files_in_repository("username/repo", subdir="data", pattern="*.json")
    """
    return [
        path for _, path in list_repo_files_in_repository(
            repo_id=repo_id,
            repo_type=repo_type,
            subdir=subdir,
            pattern=pattern,
            revision=revision,
            raise_when_base_not_exist=raise_when_base_not_exist,
            hf_token=hf_token,
        )
    ]

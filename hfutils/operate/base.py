import fnmatch
import os
from functools import lru_cache
from typing import Literal, List, Optional

from huggingface_hub import HfApi, HfFileSystem

from hfutils.utils import parse_hf_fs_path

RepoTypeTyping = Literal['dataset', 'model', 'space']
REPO_TYPES = ['dataset', 'model', 'space']


@lru_cache()
def _get_hf_token() -> Optional[str]:
    """
    Retrieve the Hugging Face token from the environment variable.

    :return: The Hugging Face token.
    :rtype: Optional[str]
    """
    return os.environ.get('HF_TOKEN')


@lru_cache()
def get_hf_client(hf_token: Optional[str] = None) -> HfApi:
    """
    Get the Hugging Face API client.

    :param hf_token: Huggingface token for API client, use ``HF_TOKEN`` variable if not assigned.
    :type hf_token: str, optional

    :return: The Hugging Face API client.
    :rtype: HfApi
    """
    return HfApi(token=hf_token or _get_hf_token())


@lru_cache()
def get_hf_fs(hf_token: Optional[str] = None) -> HfFileSystem:
    """
    Get the Hugging Face file system.

    :param hf_token: Huggingface token for API client, use ``HF_TOKEN`` variable if not assigned.
    :type hf_token: str, optional

    :return: The Hugging Face file system.
    :rtype: HfFileSystem
    """
    # use_listings_cache=False is necessary
    # or the result of glob and ls will be cached, the unittest will down
    return HfFileSystem(token=hf_token or _get_hf_token(), use_listings_cache=False)


_DEFAULT_IGNORE_PATTERNS = ['.git*']
_IGNORE_PATTERN_UNSET = object()


def _is_file_ignored(file_segments: List[str], ignore_patterns: List[str]) -> bool:
    """
    Check if a file should be ignored based on the given ignore patterns.

    :param file_segments: The segments of the file path.
    :type file_segments: List[str]
    :param ignore_patterns: List of file patterns to ignore.
    :type ignore_patterns: List[str]

    :return: True if the file should be ignored, False otherwise.
    :rtype: bool
    """
    for segment in file_segments:
        for pattern in ignore_patterns:
            if fnmatch.fnmatch(segment, pattern):
                return True

    return False


def list_files_in_repository(repo_id: str, repo_type: RepoTypeTyping = 'dataset',
                             subdir: str = '', revision: str = 'main',
                             ignore_patterns: List[str] = _IGNORE_PATTERN_UNSET,
                             hf_token: Optional[str] = None) -> List[str]:
    """
    List files in a Hugging Face repository based on the given parameters.

    :param repo_id: The identifier of the repository.
    :type repo_id: str
    :param repo_type: The type of the repository ('dataset', 'model', 'space').
    :type repo_type: RepoTypeTyping
    :param subdir: The subdirectory to list files from.
    :type subdir: str
    :param revision: The revision of the repository (e.g., branch, tag, commit hash).
    :type revision: str
    :param ignore_patterns: List of file patterns to ignore.
    :type ignore_patterns: List[str]
    :param hf_token: Huggingface token for API client, use ``HF_TOKEN`` variable if not assigned.
    :type hf_token: str, optional

    :return: A list of file paths.
    :rtype: List[str]
    """
    if ignore_patterns is _IGNORE_PATTERN_UNSET:
        ignore_patterns = _DEFAULT_IGNORE_PATTERNS
    hf_fs = get_hf_fs(hf_token)
    if repo_type == 'model':
        repo_root_path = repo_id
    elif repo_type == 'dataset':
        repo_root_path = f'datasets/{repo_id}'
    elif repo_type == 'space':
        repo_root_path = f'spaces/{repo_id}'
    else:
        raise ValueError(f'Invalid repo_type - {repo_type!r}.')
    if subdir and subdir != '.':
        repo_root_path = f'{repo_root_path}/{subdir}'

    try:
        _exist_files = [
            parse_hf_fs_path(file).filename
            for file in hf_fs.glob(f'{repo_root_path}/**', revision=revision)
        ]
    except FileNotFoundError:
        return []
    if subdir and subdir != '.':
        _exist_files = [os.path.relpath(file, subdir) for file in _exist_files]

    _exist_ps = sorted([(file, file.split('/')) for file in _exist_files], key=lambda x: x[1])
    retval = []
    for i, (file, segments) in enumerate(_exist_ps):
        if i < len(_exist_ps) - 1 and segments == _exist_ps[i + 1][1][:len(segments)]:
            continue
        if file != '.':
            if not _is_file_ignored(segments, ignore_patterns):
                retval.append('/'.join(segments))

    return retval

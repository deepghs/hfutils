import fnmatch
import logging
import os
import re
from functools import lru_cache
from typing import Literal, List, Optional, Union, Iterator

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


def list_all_with_pattern(
        repo_id: str, pattern: str = '**/*', repo_type: RepoTypeTyping = 'dataset',
        revision: str = 'main', startup_batch: int = 500, batch_factor: float = 0.8,
        hf_token: Optional[str] = None, silent: bool = False
) -> Iterator[Union[RepoFile, RepoFolder]]:
    hf_fs = get_hf_fs(hf_token=hf_token)
    hf_client = get_hf_client(hf_token=hf_token)

    try:
        paths = [
            parse_hf_fs_path(path).filename
            for path in hf_fs.glob(hf_fs_path(
                repo_id=repo_id,
                repo_type=repo_type,
                filename=pattern,
                revision=revision,
            ))
        ]
    except FileNotFoundError:
        return

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
                logging.info(f'Reducing batch size {batch_size} --> {new_batch_size} ...')
                batch_size = new_batch_size
                continue
            raise
        else:
            progress.update(len(all_items))
            offset += len(all_items)
            yield from all_items


def list_files_in_repository(
        repo_id: str, repo_type: RepoTypeTyping = 'dataset',
        subdir: str = '', pattern: str = '**/*', revision: str = 'main',
        ignore_patterns: List[str] = _IGNORE_PATTERN_UNSET,
        hf_token: Optional[str] = None, silent: bool = False) -> List[str]:
    """
    List files in a Hugging Face repository based on the given parameters.

    :param repo_id: The identifier of the repository.
    :type repo_id: str
    :param repo_type: The type of the repository ('dataset', 'model', 'space').
    :type repo_type: RepoTypeTyping
    :param subdir: The subdirectory to list files from.
    :type subdir: str
    :param pattern: Wildcard pattern of the target files.
    :type pattern: str
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
                result.append(path)

    return result

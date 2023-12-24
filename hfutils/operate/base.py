import fnmatch
import os
from functools import lru_cache
from typing import Literal, List

from huggingface_hub import HfApi, HfFileSystem

RepoTypeTyping = Literal['dataset', 'model', 'space']


@lru_cache()
def get_hf_client() -> HfApi:
    return HfApi(token=os.environ.get('HF_TOKEN'))


@lru_cache()
def get_hf_fs() -> HfFileSystem:
    # use_listings_cache=False is necessary
    # or the result of glob and ls will be cached, the unittest will down
    return HfFileSystem(token=os.environ.get('HF_TOKEN'), use_listings_cache=False)


_DEFAULT_IGNORE_PATTERNS = ['.git*']
_IGNORE_PATTERN_UNSET = object()


def _is_file_ignored(file_segments: List[str], ignore_patterns: List[str]) -> bool:
    for segment in file_segments:
        for pattern in ignore_patterns:
            if fnmatch.fnmatch(segment, pattern):
                return True

    return False


def list_files_in_repository(repo_id: str, repo_type: RepoTypeTyping = 'dataset',
                             subdir: str = '', revision: str = 'main',
                             ignore_patterns: List[str] = _IGNORE_PATTERN_UNSET):
    if ignore_patterns is _IGNORE_PATTERN_UNSET:
        ignore_patterns = _DEFAULT_IGNORE_PATTERNS
    hf_fs = get_hf_fs()
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
            os.path.relpath(file, repo_root_path)
            for file in hf_fs.glob(f'{repo_root_path}/**', revision=revision)
        ]
    except FileNotFoundError:
        return []
    _exist_ps = sorted([(file, file.split('/')) for file in _exist_files], key=lambda x: x[1])
    retval = []
    for i, (file, segments) in enumerate(_exist_ps):
        if i < len(_exist_ps) - 1 and segments == _exist_ps[i + 1][1][:len(segments)]:
            continue
        if file != '.':
            if not _is_file_ignored(segments, ignore_patterns):
                retval.append('/'.join(segments))

    return retval

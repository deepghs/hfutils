import json
import os
import re
from dataclasses import dataclass
from functools import lru_cache
from typing import Optional, Dict, Set, Literal

RepoTypeTyping = Literal['dataset', 'model', 'space']


def hf_normpath(path) -> str:
    return re.sub(
        r'[\\/]+', '/',
        os.path.relpath(os.path.normpath(os.path.join(os.sep, path)), os.sep)
    )


def hf_fs_path(repo_id: str, filename: str,
               repo_type: RepoTypeTyping = 'dataset', revision: Optional[str] = None):
    filename = hf_normpath(filename)
    if repo_type == 'dataset':
        prefix = 'datasets/'
    elif repo_type == 'space':
        prefix = 'spaces/'
    else:
        prefix = ''

    if revision is not None:
        revision_text = f'@{revision}'
    else:
        revision_text = ''

    return f'{prefix}{repo_id}{revision_text}/{filename}'


@lru_cache()
def _irregular_repos() -> Dict[RepoTypeTyping, Set[str]]:
    with open(os.path.join(os.path.dirname(__file__), 'irregular_repo.json'), 'r') as f:
        data = json.load(f)
        return {
            'model': set(data['models']),
            'dataset': set(data['datasets']),
            'space': set(data['spaces']),
        }


_RE_IR_PATH = re.compile(
    r'^(?P<repo_id>[^@/]+)(@(?P<revision>[^@/]+))?(/(?P<filename>[\s\S]+))?$')
_RE_PATH = re.compile(
    r'^(?P<repo_id>[^@/]+/[^@/]+)(@(?P<revision>[^@/]+))?(/(?P<filename>[\s\S]+))?$')


@dataclass
class HfFileSystemPath:
    repo_id: str
    filename: str
    repo_type: RepoTypeTyping
    revision: Optional[str]


def parse_hf_fs_path(path: str):
    origin_path = path
    repo_type: RepoTypeTyping
    if path.startswith('datasets/'):
        repo_type = 'dataset'
        path = path[len('datasets/'):]
    elif path.startswith('spaces/'):
        repo_type = 'space'
        path = path[len('spaces/'):]
    else:
        repo_type = 'model'

    matching = _RE_IR_PATH.fullmatch(path)
    if matching:
        if matching.group('repo_id') not in _irregular_repos()[repo_type]:
            matching = None
    if not matching:
        matching = _RE_PATH.fullmatch(path)

    if matching:
        repo_id = matching.group('repo_id')
        revision = matching.group('revision') or None
        filename = hf_normpath(matching.group('filename') or '.')
        return HfFileSystemPath(repo_id, filename, repo_type, revision)
    else:
        raise ValueError(f'Invalid huggingface filesystem path - {origin_path!r}.')

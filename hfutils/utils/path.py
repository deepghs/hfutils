"""
This module provides utilities for working with Hugging Face filesystem paths.
It includes functions for normalizing paths, constructing Hugging Face filesystem paths,
and parsing those paths into structured components. Additionally, it manages
irregular repositories through caching and provides a data class for representing
Hugging Face filesystem paths.
"""

import json
import os
import re
from dataclasses import dataclass
from functools import lru_cache
from typing import Optional, Dict, Set, Literal

RepoTypeTyping = Literal['dataset', 'model', 'space']


def hf_normpath(path) -> str:
    """
    Normalize a given path.

    This function takes a path as input and normalizes it by removing any redundant
    separators and converting it to a relative path. This can be useful for ensuring
    consistent path formatting across different operating systems.

    :param path: The path to normalize.
    :type path: Any

    :return: The normalized path.
    :rtype: str
    """
    return re.sub(
        r'[\\/]+', '/',
        os.path.relpath(os.path.normpath(os.path.join(os.sep, path)), os.sep)
    )


def hf_fs_path(repo_id: str, filename: str,
               repo_type: RepoTypeTyping = 'dataset', revision: Optional[str] = None) -> str:
    """
    Get the huggingface filesystem path.

    This function constructs a Hugging Face filesystem path from the given repository ID,
    filename, repository type, and optional revision. It ensures that the path is formatted
    correctly according to the Hugging Face conventions.

    :param repo_id: The repository ID.
    :type repo_id: str

    :param filename: The filename.
    :type filename: str

    :param repo_type: The type of repository. (default: 'dataset')
    :type repo_type: RepoTypeTyping

    :param revision: The revision of the repository. (default: None)
    :type revision: Optional[str]

    :return: The huggingface filesystem path.
    :rtype: str
    """
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
    """
    Get irregular repositories.

    This function reads a JSON file containing a list of irregular repositories for
    different types (models, datasets, spaces) and returns them as a dictionary.
    It caches the results for efficiency.

    :return: A dictionary containing irregular repositories.
    :rtype: Dict[RepoTypeTyping, Set[str]]
    """
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
    r'^(?P<repo_id>[^@/]+/[^@/]+)(@(?P<revision>(refs/pr/\d+|[^@/]+)))?(/(?P<filename>[\s\S]+))?$')


@dataclass
class HfFileSystemPath:
    """
    Huggingface FileSystem Path.

    This data class represents a Hugging Face filesystem path, encapsulating the
    repository ID, filename, repository type, and optional revision. It is used
    to provide a structured representation of filesystem paths used in Hugging Face.

    :param repo_id: The repository ID.
    :type repo_id: str

    :param filename: The filename.
    :type filename: str

    :param repo_type: The type of repository.
    :type repo_type: RepoTypeTyping

    :param revision: The revision of the repository.
    :type revision: Optional[str]
    """
    repo_id: str
    filename: str
    repo_type: RepoTypeTyping
    revision: Optional[str]


def parse_hf_fs_path(path: str) -> HfFileSystemPath:
    """
    Parse the huggingface filesystem path.

    This function takes a Hugging Face filesystem path as input and parses it into
    its components: repository ID, filename, repository type, and revision. It validates
    the path format and raises an error if the path is invalid.

    :param path: The path to parse.
    :type path: str

    :return: The parsed huggingface filesystem path.
    :rtype: HfFileSystemPath
    :raises ValueError: If this path is invalid.
    """
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

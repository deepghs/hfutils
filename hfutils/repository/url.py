"""
This module provides functions for generating URLs related to Hugging Face Hub repositories.

It includes functions to create URLs for repository paths and files, which can be useful
for accessing and referencing resources within Hugging Face Hub repositories.
"""

from typing import Optional
from urllib.parse import quote_plus, urljoin

from .base import hf_hub_repo_url
from ..utils.path import RepoTypeTyping, hf_normpath


def hf_hub_repo_path_url(repo_id: str, path: str, repo_type: RepoTypeTyping = 'dataset',
                         revision: str = 'main', endpoint: Optional[str] = None) -> str:
    """
    Generate the URL for a path within a Hugging Face Hub repository.

    This function constructs a URL that points to a specific path within a Hugging Face Hub repository.
    It's useful for creating links to directories or files in the repository's web interface.

    :param repo_id: The repository ID (e.g., 'username/repo-name').
    :type repo_id: str
    :param path: The path within the repository to generate the URL for.
    :type path: str
    :param repo_type: The type of the repository. Defaults to 'dataset'.
    :type repo_type: RepoTypeTyping, optional
    :param revision: The revision (branch, tag, or commit) to use. Defaults to 'main'.
    :type revision: str, optional
    :param endpoint: The API endpoint to use. If None, the default endpoint will be used.
    :type endpoint: str, optional

    :return: The URL for the specified path in the Hugging Face Hub repository.
    :rtype: str

    :example:
        >>> url = hf_hub_repo_path_url('username/my-dataset', 'data/train.csv')
        >>> print(url)
        https://huggingface.co/datasets/username/my-dataset/tree/main/data/train.csv
    """
    repo_url = hf_hub_repo_url(
        repo_id=repo_id,
        repo_type=repo_type,
        endpoint=endpoint,
    )
    return urljoin(repo_url + '/', hf_normpath(f'tree/{quote_plus(revision)}/{hf_normpath(path)}'))


def hf_hub_repo_file_url(repo_id: str, path: str, repo_type: RepoTypeTyping = 'dataset',
                         revision: str = 'main', endpoint: Optional[str] = None) -> str:
    """
    Generate the URL for a file within a Hugging Face Hub repository.

    This function constructs a URL that points to a specific file within a Hugging Face Hub repository.
    It's useful for creating links to view files in the repository's web interface.

    :param repo_id: The repository ID (e.g., 'username/repo-name').
    :type repo_id: str
    :param path: The path to the file within the repository.
    :type path: str
    :param repo_type: The type of the repository. Defaults to 'dataset'.
    :type repo_type: RepoTypeTyping, optional
    :param revision: The revision (branch, tag, or commit) to use. Defaults to 'main'.
    :type revision: str, optional
    :param endpoint: The API endpoint to use. If None, the default endpoint will be used.
    :type endpoint: str, optional

    :return: The URL for the specified file in the Hugging Face Hub repository.
    :rtype: str

    :example:
        >>> url = hf_hub_repo_file_url('username/my-model', 'config.json')
        >>> print(url)
        https://huggingface.co/username/my-model/blob/main/config.json

    .. note::
        This is not the downloadable URL of the file in the repository.
        For downloading URLs, use :func:`huggingface_hub.hf_hub_url`.
    """
    repo_url = hf_hub_repo_url(
        repo_id=repo_id,
        repo_type=repo_type,
        endpoint=endpoint,
    )
    return urljoin(repo_url + '/', hf_normpath(f'blob/{quote_plus(revision)}/{hf_normpath(path)}'))

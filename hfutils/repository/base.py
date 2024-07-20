"""
This module provides utility functions for working with Hugging Face Hub repositories and Git.

It includes functions to:

1. Generate Hugging Face Hub repository URLs.
2. Check Git and Git LFS installations.

The module uses the `git_info` function from the `hbutils.system` package and constants from `huggingface_hub`.
"""

from typing import Optional

from hbutils.system import git_info
from huggingface_hub.constants import ENDPOINT

from ..utils.path import RepoTypeTyping


def hf_hub_repo_url(repo_id: str, repo_type: RepoTypeTyping = 'dataset', endpoint: Optional[str] = None) -> str:
    """
    Generate a Hugging Face Hub repository URL.

    :param repo_id: The repository ID.
    :type repo_id: str
    :param repo_type: The type of repository. Can be 'model', 'dataset', or 'space'. Defaults to 'dataset'.
    :type repo_type: RepoTypeTyping
    :param endpoint: The Hugging Face Hub endpoint. If None, uses the default ENDPOINT.
    :type endpoint: Optional[str]

    :return: The full URL for the specified Hugging Face Hub repository.
    :rtype: str

    :raises ValueError: If an unknown repository type is provided.

    :usage:
        >>> hf_hub_repo_url('username/repo', 'model')
        'https://huggingface.co/username/repo'
        >>> hf_hub_repo_url('username/dataset', 'dataset')
        'https://huggingface.co/datasets/username/dataset'
    """
    endpoint = endpoint or ENDPOINT
    if repo_type == 'model':
        return f'{endpoint}/{repo_id}'
    elif repo_type == 'dataset':
        return f'{endpoint}/datasets/{repo_id}'
    elif repo_type == 'space':
        return f'{endpoint}/spaces/{repo_id}'
    else:
        raise ValueError(f'Unknown repository type - {repo_type!r}.')


def _check_git(requires_lfs: bool = True) -> str:
    """
    Check Git and Git LFS installations.

    This function checks if Git is installed and, optionally, if Git LFS is installed.
    The results are cached for improved performance.

    :param requires_lfs: Whether to check for Git LFS installation. Defaults to True.
    :type requires_lfs: bool

    :return: The path to the Git executable.
    :rtype: str

    :raises EnvironmentError: If Git is not installed or if Git LFS is required but not installed.

    :usage:
        >>> _check_git()
        '/usr/bin/git'
        >>> _check_git(requires_lfs=False)
        '/usr/bin/git'
    """
    info = git_info()
    if not info['installed']:
        raise EnvironmentError('Git not installed.')
    else:
        if requires_lfs and not info['lfs']['installed']:
            raise EnvironmentError('Git lfs not installed.')
        else:
            return info['exec']

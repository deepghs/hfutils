"""
This module provides functionality to rollback a Hugging Face Hub repository to a specific commit.

It includes a function to clone a repository, reset it to a specified commit, and force push the changes back to the remote repository.
"""

import logging
import os.path
import subprocess
import sys
from typing import Optional

from .base import _check_git
from .clone import hf_hub_clone
from ..utils import TemporaryDirectory
from ..utils.path import RepoTypeTyping


def hf_hub_rollback(repo_id: str, rollback_to: str,
                    repo_type: RepoTypeTyping = 'dataset', revision: str = 'main',
                    endpoint: Optional[str] = None, hf_token: Optional[str] = None, silent: bool = False):
    """
    Rollback a Hugging Face Hub repository to a specific commit.

    This function clones the repository, resets it to the specified commit, and force pushes the changes back to the remote.

    :param repo_id: The ID of the repository to rollback.
    :type repo_id: str
    :param rollback_to: The commit hash or reference to rollback to.
    :type rollback_to: str
    :param repo_type: The type of the repository ('dataset', 'model', or 'space'). Defaults to 'dataset'.
    :type repo_type: RepoTypeTyping
    :param revision: The branch or tag to clone. Defaults to 'main'.
    :type revision: str
    :param endpoint: The Hugging Face Hub endpoint. If None, uses the default endpoint.
    :type endpoint: Optional[str]
    :param hf_token: The Hugging Face authentication token. If None, attempts to use stored credentials.
    :type hf_token: Optional[str]
    :param silent: If True, suppresses command output. Defaults to False.
    :type silent: bool

    :raises subprocess.CalledProcessError: If any Git command fails during the process.

    :usage:
        >>> hf_hub_rollback('username/repo', 'abc123', repo_type='model')

    .. note::

        This function performs the following steps:

        1. Checks for Git installation (without LFS requirement).
        2. Creates a temporary directory for the operation.
        3. Clones the specified repository into the temporary directory.
        4. Resets the repository to the specified commit using 'git reset --hard'.
        5. Force pushes the changes back to the remote repository.

    .. warning::
        This operation can overwrite remote history and can not be cancelled. Use with caution.
    """
    _git = _check_git(requires_lfs=False)
    with TemporaryDirectory() as td, open(os.devnull, 'w') as nf:
        envs = {
            **os.environ,
            'GIT_LFS_SKIP_SMUDGE': '1',
            'GIT_TERMINAL_PROMPT': '0',
        }

        repo_dir = os.path.join(td, 'repo')
        hf_hub_clone(
            repo_id=repo_id,
            dst_dir=repo_dir,
            repo_type=repo_type,
            revision=revision,
            endpoint=endpoint,
            hf_token=hf_token,
            silent=silent,
            no_lfs=True,
        )

        reset_command = [_git, 'reset', '--hard', rollback_to]
        logging.info(f'Git resetting with command {reset_command!r} ...')
        process = subprocess.run(
            args=reset_command,
            stdout=nf if silent else sys.stdout,
            stderr=nf if silent else sys.stderr,
            env=envs,
            bufsize=0 if not silent else -1,
            cwd=repo_dir,
        )
        process.check_returncode()

        push_command = [_git, 'push', '-f']
        logging.info(f'Git pushing with command {push_command!r} ...')
        process = subprocess.run(
            args=push_command,
            stdout=nf if silent else sys.stdout,
            stderr=nf if silent else sys.stderr,
            env=envs,
            bufsize=0 if not silent else -1,
            cwd=repo_dir,
        )
        process.check_returncode()

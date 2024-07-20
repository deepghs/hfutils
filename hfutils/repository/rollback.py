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

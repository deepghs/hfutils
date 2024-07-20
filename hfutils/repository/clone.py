import copy
import logging
import os
import subprocess
import sys
from typing import Optional

from huggingface_hub.errors import LocalTokenNotFoundError
from urlobject import URLObject

from .base import hf_hub_repo_url, _check_git
from ..operate import get_hf_client
from ..utils.path import RepoTypeTyping


def hf_hub_clone(repo_id: str, dst_dir: str,
                 repo_type: RepoTypeTyping = 'dataset', revision: str = 'main',
                 endpoint: Optional[str] = None, hf_token: Optional[str] = None,
                 silent: bool = False, no_lfs: bool = False, max_depth: Optional[int] = None):
    _git = _check_git(requires_lfs=not no_lfs)
    hf_client = get_hf_client(hf_token)
    try:
        username = hf_client.whoami()['name']
    except LocalTokenNotFoundError:
        username = None  # anonymous mode

    clone_url = URLObject(hf_hub_repo_url(
        repo_id=repo_id,
        repo_type=repo_type,
        endpoint=endpoint,
    ))
    if username:
        clone_url = clone_url.with_username(username).with_password(hf_client.token)
    clone_url = str(clone_url)

    command = [_git, 'clone', '-b', revision]
    if max_depth is not None:
        command.extend(['--depth', str(max_depth)])
    command.extend([clone_url, dst_dir])
    logging.info(f'Cloning repository with command {command!r} ...')
    with open(os.devnull, 'w') as nf:
        envs = copy.deepcopy(os.environ)
        if no_lfs:
            envs['GIT_LFS_SKIP_SMUDGE'] = '1'
        envs['GIT_TERMINAL_PROMPT'] = '0'
        process = subprocess.run(
            args=command,
            stdout=nf if silent else sys.stdout,
            stderr=nf if silent else sys.stderr,
            env=envs,
            bufsize=0 if not silent else -1,
        )
        process.check_returncode()

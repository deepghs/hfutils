from functools import lru_cache
from typing import Optional

from hbutils.system import git_info
from huggingface_hub.constants import ENDPOINT

from ..utils.path import RepoTypeTyping


def hf_hub_repo_url(repo_id: str, repo_type: RepoTypeTyping = 'dataset', endpoint: Optional[str] = None) -> str:
    endpoint = endpoint or ENDPOINT
    if repo_type == 'model':
        return f'{endpoint}/{repo_id}'
    elif repo_type == 'dataset':
        return f'{endpoint}/datasets/{repo_id}'
    elif repo_type == 'space':
        return f'{endpoint}/spaces/{repo_id}'
    else:
        raise ValueError(f'Unknown repository type - {repo_type!r}.')


@lru_cache()
def _check_git(requires_lfs: bool = True) -> str:
    info = git_info()
    if not info['installed']:
        raise EnvironmentError('Git not installed.')
    else:
        if requires_lfs and not info['lfs']['installed']:
            raise EnvironmentError('Git lfs not installed.')
        else:
            return info['exec']

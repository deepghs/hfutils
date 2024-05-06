import os
import re
from typing import Optional

from hfutils.operate.base import RepoTypeTyping


def hf_normpath(path) -> str:
    return re.sub(
        r'[\\/]+', '/',
        os.path.relpath(
            os.path.normpath(os.path.join(os.path.pathsep, path)),
            os.path.pathsep
        )
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

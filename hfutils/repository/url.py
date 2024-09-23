from typing import Optional
from urllib.parse import quote_plus, urljoin

from .base import hf_hub_repo_url
from ..utils.path import RepoTypeTyping, hf_normpath


def hf_hub_repo_path_url(repo_id: str, path: str, repo_type: RepoTypeTyping = 'dataset',
                         revision: str = 'main', endpoint: Optional[str] = None) -> str:
    # url of the huggingface repository path
    repo_url = hf_hub_repo_url(
        repo_id=repo_id,
        repo_type=repo_type,
        endpoint=endpoint,
    )
    return urljoin(repo_url + '/', hf_normpath(f'tree/{quote_plus(revision)}/{hf_normpath(path)}'))


def hf_hub_repo_file_url(repo_id: str, path: str, repo_type: RepoTypeTyping = 'dataset',
                         revision: str = 'main', endpoint: Optional[str] = None) -> str:
    # url of the huggingface repository file
    # note: this is not the downloadable url of the file in repository,
    #       if you're looking for url for downloading, use :func:`huggingface_hub.hf_hub_url`.
    repo_url = hf_hub_repo_url(
        repo_id=repo_id,
        repo_type=repo_type,
        endpoint=endpoint,
    )
    return urljoin(repo_url + '/', hf_normpath(f'blob/{quote_plus(revision)}/{hf_normpath(path)}'))

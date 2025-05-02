import logging
from concurrent.futures import ThreadPoolExecutor
from typing import Optional, List

import requests
from huggingface_hub import hf_hub_download
from huggingface_hub.hf_api import RepoFile
from tqdm import tqdm

from .base import RepoTypeTyping, list_repo_files_in_repository
from .download import _IGNORE_PATTERN_UNSET
from ..utils import hf_normpath


def hf_warmup_file(repo_id: str, filename: str, repo_type: RepoTypeTyping = 'dataset', revision: str = 'main',
                   hf_token: Optional[str] = None):
    # the same as hf_hub_download
    return hf_hub_download(
        repo_id=repo_id,
        repo_type=repo_type,
        filename=filename,
        revision=revision,
        token=hf_token,
    )


def hf_warmup_directory(repo_id: str, dir_in_repo: str = '.', pattern: str = '**/*',
                        repo_type: RepoTypeTyping = 'dataset', revision: str = 'main',
                        silent: bool = False, ignore_patterns: List[str] = _IGNORE_PATTERN_UNSET,
                        max_workers: int = 8, max_retries: int = 5, hf_token: Optional[str] = None):
    files = list_repo_files_in_repository(
        repo_id=repo_id,
        repo_type=repo_type,
        subdir=dir_in_repo,
        pattern=pattern,
        revision=revision,
        ignore_patterns=ignore_patterns,
        hf_token=hf_token,
    )
    progress = tqdm(files, silent=silent, desc=f'Downloading {dir_in_repo!r} ...')

    def _warmup_one_file(repo_file: RepoFile, rel_file: str):
        _ = repo_file
        try:
            file_in_repo = hf_normpath(f'{dir_in_repo}/{rel_file}')
            tries = 0
            while True:
                try:
                    hf_hub_download(
                        repo_id=repo_id,
                        repo_type=repo_type,
                        filename=file_in_repo,
                        revision=revision,
                        token=hf_token,
                    )
                except requests.exceptions.RequestException as err:
                    if tries < max_retries:
                        tries += 1
                        logging.warning(f'Download {rel_file!r} failed, retry ({tries}/{max_retries}) - {err!r}.')
                    else:
                        raise
                else:
                    break
            progress.update()
        except Exception as err:
            logging.exception(f'Unexpected error when downloading {rel_file!r} - {err!r}')

    tp = ThreadPoolExecutor(max_workers=max_workers)
    for item, file in files:
        tp.submit(_warmup_one_file, item, file)
    tp.shutdown(wait=True)

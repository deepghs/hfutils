import os
from contextlib import contextmanager
from typing import List, Optional, ContextManager

import pytest
from hbutils.system import TemporaryDirectory
from huggingface_hub import HfApi


@contextmanager
def mock_repository_cachedir(mock_files: List[str], commit_ids: List[Optional[str]],
                             repository: str = 'deepghs/hfcache_test_target_repo') -> ContextManager[str]:
    with TemporaryDirectory() as td:
        cache_dir = os.path.join(td, 'hub')
        os.makedirs(cache_dir, exist_ok=True)

        hf_client = HfApi()
        for commit_id in commit_ids:
            for filename in mock_files:
                hf_client.hf_hub_download(
                    repo_id=repository,
                    repo_type='dataset',
                    filename=filename,
                    revision=commit_id,
                    cache_dir=cache_dir,
                )

        yield cache_dir


@pytest.fixture(scope='function')
def simple_cachedir():
    with mock_repository_cachedir(
            mock_files=[
                'index_tag_aliases.csv',
            ],
            commit_ids=[
                None,
                '6705b4fec34fafa232602d473a30ebefc468fd55',
            ],
    ) as cache_dir:
        yield cache_dir


@pytest.fixture(scope='function')
def non_exist_cachedir():
    with TemporaryDirectory() as td:
        hf_home_dir = os.path.join(td, '.cache')
        yield os.path.join(hf_home_dir, 'hub')

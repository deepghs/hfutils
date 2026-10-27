import test.testings.hfvcr.env  # noqa: F401  (must stay the first import: it prepares huggingface_hub's environment)

pytest_plugins = ['test.testings.hfvcr.plugin']

import re
import sys

import pytest
from hbutils.random import random_sha1_with_timestamp

from hfutils.operate.base import get_hf_fs, get_hf_client
from test.testings import get_testfile, dir_compare


@pytest.fixture(autouse=True)
def _each_test_has_its_own_hub_cache(monkeypatch, tmp_path):
    """
    The cache of ``huggingface_hub`` on disk is shared by everything that runs in a process. A test that finds a file in it sends no
    ``GET`` for it, so its cassette would hold the download only if it happened to run first: replay, under another order or on another
    xdist worker, would miss it. Every test gets an empty cache of its own.
    """
    from huggingface_hub import constants
    cache = str(tmp_path / 'hub')
    for name in ('HF_HUB_CACHE', 'HUGGINGFACE_HUB_CACHE'):
        if hasattr(constants, name):
            monkeypatch.setattr(constants, name, cache)
    for module in ('huggingface_hub.file_download', 'huggingface_hub.hf_api', 'huggingface_hub._snapshot_download',
                   'huggingface_hub.utils._cache_manager'):
        loaded = sys.modules.get(module)  # some versions copied the value into the module when they were imported
        for name in ('HF_HUB_CACHE', 'HUGGINGFACE_HUB_CACHE'):
            if loaded is not None and hasattr(loaded, name):
                monkeypatch.setattr(loaded, name, cache)
    yield cache


@pytest.fixture(autouse=True)
def _hfutils_caches_start_empty():
    """
    hfutils keeps the index of an archive in memory between calls. A test that finds it there asks the Hub for less than the very
    same test would alone, so what its cassette holds would depend on which tests ran before it in that process (and replay,
    under another order or another xdist worker, would miss the requests). Every test starts with the caches empty.
    """
    from hfutils.index import hf_tar_cache_reset, tar_cache_reset
    hf_tar_cache_reset()
    tar_cache_reset()
    yield


@pytest.fixture()
def raw_dir():
    return get_testfile('raw')


@pytest.fixture()
def check_unpack_dir(raw_dir):
    def _check(directory):
        dir_compare(raw_dir, directory)
        # for file in walk_files(raw_dir):
        #     src_file = os.path.join(raw_dir, file)
        #     dst_file = os.path.join(directory, file)
        #     assert os.path.exists(dst_file), f'File {dst_file!r} not exists!'
        #     assert pathlib.Path(src_file).read_text().splitlines(keepends=False) == \
        #            pathlib.Path(dst_file).read_text().splitlines(keepends=False)

    return _check


_REPO_URL_PATTERN = re.compile(r'^https://huggingface.co/datasets/(?P<repo>[a-zA-Z\d/_\-]+)$')


@pytest.fixture()
def hf_client():
    return get_hf_client()


@pytest.fixture()
def hf_fs():
    return get_hf_fs()


@pytest.fixture()
def hf_repo(hf_client, hf_vcr):
    """
    A throw-away dataset repository, the first fixture of the multi-step scenarios.

    Its traffic lives in two segments of its own (``repo`` and ``repo.cleanup``); the random name is a recorded
    variable, so a replay talks about exactly the repository the recording created.
    """
    with hf_vcr.segment('repo') as seg:
        repo_name = seg.var('name', lambda: f'test_repo_{random_sha1_with_timestamp()}')
        url = hf_client.create_repo(repo_name, repo_type='dataset', exist_ok=True)
        repo_name = _REPO_URL_PATTERN.fullmatch(url).group('repo')
    try:
        yield repo_name
    finally:
        with hf_vcr.segment('repo.cleanup'):
            hf_client.delete_repo(repo_name, repo_type='dataset')

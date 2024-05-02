import re

import pytest
from hbutils.random import random_sha1_with_timestamp

from hfutils.operate.base import get_hf_fs, get_hf_client
from test.testings import get_testfile, dir_compare


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
def hf_repo(hf_client):
    repo_name = f'test_repo_{random_sha1_with_timestamp()}'
    url = hf_client.create_repo(repo_name, repo_type='dataset', exist_ok=True)
    repo_name = _REPO_URL_PATTERN.fullmatch(url).group('repo')
    try:
        yield repo_name
    finally:
        hf_client.delete_repo(repo_name, repo_type='dataset')

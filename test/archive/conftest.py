import os.path
import pathlib

import pytest

from hfutils.utils import walk_files
from test.testings import get_testfile


@pytest.fixture()
def raw_dir():
    return get_testfile('raw')


@pytest.fixture()
def check_unpack_dir(raw_dir):
    def _check(directory):
        for file in walk_files(raw_dir):
            src_file = os.path.join(raw_dir, file)
            dst_file = os.path.join(directory, file)
            assert os.path.exists(dst_file), f'File {dst_file!r} not exists!'
            assert pathlib.Path(src_file).read_bytes() == pathlib.Path(dst_file).read_bytes()

    return _check

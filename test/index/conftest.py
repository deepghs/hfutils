import pytest
from hbutils.system import TemporaryDirectory

from hfutils.operate import download_directory_as_directory


@pytest.fixture(scope='module')
def local_narugo_test_cos5t_tars():
    with TemporaryDirectory() as td:
        download_directory_as_directory(
            repo_id='narugo/test_cos5t_tars',
            repo_type='dataset',
            local_directory=td,
        )
        yield td

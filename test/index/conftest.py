import pytest
from hbutils.system import TemporaryDirectory

from hfutils.operate import download_directory_as_directory


@pytest.fixture(scope='module')
def local_narugo_test_cos5t_tars(hf_vcr_session):
    # a module scoped fixture belongs to no test, so its traffic lives in a world shared by the tests that use it
    with TemporaryDirectory() as td, hf_vcr_session.world('narugo_test_cos5t_tars'):
        download_directory_as_directory(
            repo_id='narugo1992/test_cos5t_tars',
            repo_type='dataset',
            local_directory=td,
        )
        yield td

import os.path
import zipfile

import pytest
from hbutils.testing import isolated_directory, disable_output

from hfutils.archive import get_archive_type, get_archive_extname, archive_pack, archive_unpack
from test.testings import get_testfile


@pytest.fixture()
def raw_zip():
    return get_testfile('raw.zip')


@pytest.mark.unittest
class TestArchiveZip:
    def test_get_archive_type(self):
        assert get_archive_type(os.path.join('1.zip')) == 'zip'
        assert get_archive_type(os.path.join('111', 'f.zip')) == 'zip'

    def test_get_archive_extname(self):
        assert get_archive_extname('zip') == '.zip'

    def test_archive_pack(self, raw_dir, check_unpack_dir):
        with isolated_directory():
            with disable_output():
                archive_pack('zip', raw_dir, 'pack.zip')

            os.makedirs('dst', exist_ok=True)
            with zipfile.ZipFile('pack.zip', 'r') as zf:
                zf.extractall('dst')
            check_unpack_dir('dst')

    def test_archive_unpack(self, raw_zip, check_unpack_dir):
        with isolated_directory():
            with disable_output():
                archive_unpack(raw_zip, '.')
            check_unpack_dir('.')

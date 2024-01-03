import os.path
import tarfile

import pytest
from hbutils.testing import isolated_directory, disable_output

from hfutils.archive import get_archive_type, get_archive_extname, archive_pack, archive_unpack
from test.testings import get_testfile


@pytest.fixture()
def raw_tar():
    return get_testfile('raw.tar')


@pytest.mark.unittest
class TestArchiveTar:
    def test_get_archive_type(self):
        assert get_archive_type(os.path.join('1.tar')) == 'tar'
        assert get_archive_type(os.path.join('111', 'f.tar')) == 'tar'

    def test_get_archive_extname(self):
        assert get_archive_extname('tar') == '.tar'

    @pytest.mark.parametrize(['type_', 'ext'], [
        ('tar', '.tar'),
        ('gztar', '.tar.gz'),
        ('bztar', '.tar.bz2'),
        ('xztar', '.tar.xz'),
    ])
    def test_archive_pack_tar(self, raw_dir, check_unpack_dir, type_, ext):
        with isolated_directory():
            with disable_output():
                archive_pack(type_, raw_dir, f'pack{ext}')

            os.makedirs('dst', exist_ok=True)
            with tarfile.open(f'pack{ext}') as tar:
                tar.extractall('dst')
            check_unpack_dir('dst')

    @pytest.mark.parametrize(['type_', 'ext'], [
        ('tar', '.tar'),
        ('gztar', '.tar.gz'),
        ('bztar', '.tar.bz2'),
        ('xztar', '.tar.xz'),
    ])
    def test_archive_unpack(self, check_unpack_dir, type_, ext):
        with isolated_directory():
            with disable_output():
                archive_unpack(get_testfile(f'raw{ext}'), '.')
            check_unpack_dir('.')

    @pytest.mark.parametrize(['type_', 'ext'], [
        ('tar', '.tar'),
        ('gztar', '.tar.gz'),
        ('bztar', '.tar.bz2'),
        ('xztar', '.tar.xz'),
    ])
    def test_archive_unpack_password_ignore(self, check_unpack_dir, type_, ext):
        with isolated_directory():
            with disable_output(), pytest.warns(UserWarning):
                archive_unpack(get_testfile(f'raw{ext}'), '.', password='password')
            check_unpack_dir('.')

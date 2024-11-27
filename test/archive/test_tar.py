import glob
import os.path
import tarfile

import pytest
from hbutils.testing import isolated_directory, disable_output, tmatrix

from hfutils.archive import get_archive_type, get_archive_extname, archive_pack, archive_unpack, archive_writer
from hfutils.utils import walk_files
from test.testings import get_testfile, dir_compare


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
            origin_files = len(list(walk_files(raw_dir)))
            assert origin_files > 0
            with disable_output():
                archive_pack(type_, raw_dir, f'pack{ext}')
            assert len(list(walk_files(raw_dir))) == origin_files

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
    def test_archive_pack_tar_clear(self, raw_dir, check_unpack_dir, type_, ext):
        with isolated_directory({'test_dir': raw_dir}):
            assert len(list(walk_files(raw_dir))) > 0
            with disable_output():
                archive_pack(type_, 'test_dir', f'pack{ext}', clear=True)
            assert len(list(walk_files('test_dir'))) == 0

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

    @pytest.mark.parametrize(*tmatrix({
        'ext': ['bin', 'binary', 'bst'],
        ('type_', 'type_ext'): [
            ('tar', '.tar'),
            ('gztar', '.tar.gz'),
            ('bztar', '.tar.bz2'),
            ('xztar', '.tar.xz'),
        ],
    }))
    def test_archive_writer(self, ext, type_, type_ext):
        src_dir = get_testfile('complex_directory')
        dst_dir = get_testfile(f'complex_directory_{ext}')

        with isolated_directory():
            archive_file = f'archive.{type_ext}'
            with archive_writer(type_, archive_file) as af:
                for file in glob.glob(os.path.join(src_dir, '**', f'*.{ext}'), recursive=True):
                    af.add(file, os.path.basename(file))

            archive_unpack(archive_file, '.', silent=True)
            os.remove(archive_file)
            dir_compare('.', dst_dir)

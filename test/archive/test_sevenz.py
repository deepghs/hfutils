import glob
import os.path
from unittest import skipUnless

import pytest
from hbutils.testing import isolated_directory, disable_output, tmatrix

from hfutils.archive import get_archive_type, get_archive_extname, archive_pack, archive_unpack, archive_writer
from hfutils.utils import walk_files
from test.testings import get_testfile, dir_compare

try:
    import py7zr
except ImportError:  # pragma: no cover
    py7zr = None


@pytest.fixture()
def raw_7z():
    return get_testfile('raw.7z')


@pytest.fixture()
def raw_password_7z():
    return get_testfile('raw-password.7z')


@pytest.mark.unittest
class TestArchive7z:
    @skipUnless(py7zr, 'py7zr module required.')
    def test_get_archive_type(self):
        assert get_archive_type(os.path.join('1.7z')) == '7z'
        assert get_archive_type(os.path.join('111', 'f.7z')) == '7z'

    @skipUnless(not py7zr, 'No py7zr module required.')
    def test_get_archive_type_no_7z(self):
        with pytest.raises(ValueError):
            _ = get_archive_type(os.path.join('1.7z'))
        with pytest.raises(ValueError):
            _ = get_archive_type(os.path.join('111', 'f.7z'))

    @skipUnless(py7zr, 'py7zr module required.')
    def test_get_archive_extname(self):
        assert get_archive_extname('7z') == '.7z'

    @skipUnless(not py7zr, 'No py7zr module required.')
    def test_get_archive_extname_no_7z(self):
        with pytest.raises(ValueError):
            _ = get_archive_extname('7z')

    @skipUnless(py7zr, 'py7zr module required.')
    def test_archive_pack(self, raw_dir, check_unpack_dir):
        with isolated_directory():
            origin_files = len(list(walk_files(raw_dir)))
            assert origin_files > 0
            with disable_output():
                archive_pack('7z', raw_dir, 'pack.7z')
            assert len(list(walk_files(raw_dir))) == origin_files

            os.makedirs('dst', exist_ok=True)
            with py7zr.SevenZipFile('pack.7z', 'r') as zf:
                zf.extractall('dst')
            check_unpack_dir('dst')

    @skipUnless(py7zr, 'py7zr module required.')
    def test_archive_pack_clear(self, raw_dir, check_unpack_dir):
        with isolated_directory({'test_dir': raw_dir}):
            assert len(list(walk_files(raw_dir))) > 0
            with disable_output():
                archive_pack('7z', 'test_dir', 'pack.7z', clear=True)
            assert len(list(walk_files('test_dir'))) == 0

            os.makedirs('dst', exist_ok=True)
            with py7zr.SevenZipFile('pack.7z', 'r') as zf:
                zf.extractall('dst')
            check_unpack_dir('dst')

    @skipUnless(py7zr, 'py7zr module required.')
    def test_archive_unpack(self, raw_7z, check_unpack_dir):
        with isolated_directory():
            with disable_output():
                archive_unpack(raw_7z, '.')
            check_unpack_dir('.')

    @skipUnless(py7zr, 'py7zr module required.')
    def test_archive_unpack_with_password_failed(self, raw_password_7z):
        with isolated_directory():
            with disable_output(), pytest.raises(py7zr.exceptions.PasswordRequired):
                archive_unpack(raw_password_7z, '.')

    @skipUnless(py7zr, 'py7zr module required.')
    def test_archive_unpack_with_password(self, raw_password_7z, check_unpack_dir):
        with isolated_directory():
            with disable_output():
                archive_unpack(raw_password_7z, '.', password='password')
            check_unpack_dir('.')

    @skipUnless(py7zr, 'py7zr module required.')
    @pytest.mark.parametrize(*tmatrix({
        'ext': ['bin', 'binary', 'bst'],
        'type_': ['7z'],
    }))
    def test_archive_writer(self, ext, type_):
        src_dir = get_testfile('complex_directory')
        dst_dir = get_testfile(f'complex_directory_{ext}')

        with isolated_directory():
            archive_file = f'archive.{type_}'
            with archive_writer(type_, archive_file) as af:
                for file in glob.glob(os.path.join(src_dir, '**', f'*.{ext}'), recursive=True):
                    af.add(file, os.path.basename(file))

            archive_unpack(archive_file, '.', silent=True)
            os.remove(archive_file)
            dir_compare('.', dst_dir)

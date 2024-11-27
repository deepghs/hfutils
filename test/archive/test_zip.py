import glob
import os.path
import zipfile

import pytest
from hbutils.testing import isolated_directory, disable_output, tmatrix

from hfutils.archive import get_archive_type, get_archive_extname, archive_pack, archive_unpack, archive_writer
from hfutils.utils import walk_files
from test.testings import get_testfile, dir_compare


@pytest.fixture()
def raw_zip():
    return get_testfile('raw.zip')


@pytest.fixture()
def raw_password_zip():
    return get_testfile('raw-password.zip')


@pytest.mark.unittest
class TestArchiveZip:
    def test_get_archive_type(self):
        assert get_archive_type(os.path.join('1.zip')) == 'zip'
        assert get_archive_type(os.path.join('111', 'f.zip')) == 'zip'

    def test_get_archive_extname(self):
        assert get_archive_extname('zip') == '.zip'

    def test_archive_pack(self, raw_dir, check_unpack_dir):
        with isolated_directory():
            origin_files = len(list(walk_files(raw_dir)))
            assert origin_files > 0
            with disable_output():
                archive_pack('zip', raw_dir, 'pack.zip')
            assert len(list(walk_files(raw_dir))) == origin_files

            os.makedirs('dst', exist_ok=True)
            with zipfile.ZipFile('pack.zip', 'r') as zf:
                zf.extractall('dst')
            check_unpack_dir('dst')

    def test_archive_pack_clear(self, raw_dir, check_unpack_dir):
        with isolated_directory({'test_dir': raw_dir}):
            assert len(list(walk_files(raw_dir))) > 0
            with disable_output():
                archive_pack('zip', 'test_dir', 'pack.zip', clear=True)
            assert len(list(walk_files('test_dir'))) == 0

            os.makedirs('dst', exist_ok=True)
            with zipfile.ZipFile('pack.zip', 'r') as zf:
                zf.extractall('dst')
            check_unpack_dir('dst')

    def test_archive_unpack(self, raw_zip, check_unpack_dir):
        with isolated_directory():
            with disable_output():
                archive_unpack(raw_zip, '.')
            check_unpack_dir('.')

    def test_archive_unpack_with_password_failed(self, raw_password_zip):
        with isolated_directory():
            with disable_output(), pytest.raises(RuntimeError):
                archive_unpack(raw_password_zip, '.')

    def test_archive_unpack_with_password(self, raw_password_zip, check_unpack_dir):
        with isolated_directory():
            with disable_output():
                archive_unpack(raw_password_zip, '.', password='password')
            check_unpack_dir('.')

    @pytest.mark.parametrize(*tmatrix({
        'ext': ['bin', 'binary', 'bst'],
        'type_': ['zip'],
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

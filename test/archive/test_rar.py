import os.path
import shutil
from unittest import skipUnless

import pytest
from hbutils.testing import isolated_directory, disable_output

from hfutils.archive import get_archive_type, get_archive_extname, archive_pack, archive_unpack, archive_writer
from hfutils.utils import walk_files
from test.testings import get_testfile

try:
    import rarfile
except ImportError:  # pragma: no cover
    rarfile = None


def _rar_tool_with_passwords_available():
    # rarfile prefers unrar, then unar, then bsdtar, then 7z. bsdtar cannot open an encrypted archive, and it wins over 7z where
    # it exists (macOS), so 7z only counts when there is no bsdtar.
    if rarfile is None:
        return False
    if shutil.which('unrar') or shutil.which('unar'):
        return True
    return any(shutil.which(tool) for tool in ('7z', '7zz', '7za')) and not shutil.which('bsdtar')


# Homebrew disabled the `rar` cask on 2026-09-01 (it fails the macOS Gatekeeper check), so a macOS runner has bsdtar only.
needs_rar_tool = pytest.mark.skipif(not _rar_tool_with_passwords_available(),
                                    reason='no unrar / unar (and no 7z that rarfile would pick over bsdtar): bsdtar cannot read an encrypted rar')


@pytest.fixture()
def raw_rar():
    return get_testfile('raw.rar')


@pytest.fixture()
def raw_password_rar():
    return get_testfile('raw-password.rar')


@pytest.mark.unittest
class TestArchiveRar:
    @skipUnless(rarfile, 'rarfile module required.')
    def test_get_archive_type(self):
        assert get_archive_type(os.path.join('1.rar')) == 'rar'
        assert get_archive_type(os.path.join('111', 'f.rar')) == 'rar'

    @skipUnless(not rarfile, 'No rarfile module required.')
    def test_get_archive_type_no_rar(self):
        with pytest.raises(ValueError):
            _ = get_archive_type(os.path.join('1.rar'))
        with pytest.raises(ValueError):
            _ = get_archive_type(os.path.join('111', 'f.rar'))

    @skipUnless(rarfile, 'rarfile module required.')
    def test_get_archive_extname(self):
        assert get_archive_extname('rar') == '.rar'

    @skipUnless(not rarfile, 'No rarfile module required.')
    def test_get_archive_extname_no_rar(self):
        with pytest.raises(ValueError):
            _ = get_archive_extname('rar')

    @skipUnless(rarfile, 'rarfile module required.')
    def test_archive_pack(self, raw_dir, check_unpack_dir):
        with isolated_directory():
            origin_files = len(list(walk_files(raw_dir)))
            assert origin_files > 0
            with disable_output(), pytest.raises(RuntimeError):
                archive_pack('rar', raw_dir, 'pack.rar')
            assert len(list(walk_files(raw_dir))) == origin_files

    @skipUnless(rarfile, 'rarfile module required.')
    def test_archive_writer(self, raw_dir, check_unpack_dir):
        with isolated_directory():
            with disable_output(), pytest.raises(RuntimeError):
                archive_writer('rar', 'pack.rar')

    @skipUnless(rarfile, 'rarfile module required.')
    def test_archive_unpack(self, raw_rar, check_unpack_dir):
        with isolated_directory():
            with disable_output():
                archive_unpack(raw_rar, '.')
            check_unpack_dir('.')

    @skipUnless(rarfile, 'rarfile module required.')
    def test_archive_unpack_with_password_failed(self, raw_password_rar):
        with isolated_directory():
            with disable_output(), pytest.raises(rarfile.PasswordRequired):
                archive_unpack(raw_password_rar, '.')

    @skipUnless(rarfile, 'rarfile module required.')
    @needs_rar_tool
    def test_archive_unpack_with_password(self, raw_password_rar, check_unpack_dir):
        with isolated_directory():
            with disable_output():
                archive_unpack(raw_password_rar, '.', password='password')
            check_unpack_dir('.')

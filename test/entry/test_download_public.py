"""``hfutils download -a`` against a public repository (see ``test/operate/test_download_public.py``)."""
import pytest
from hbutils.testing import simulate_entry, isolated_directory

from hfutils.entry import hfutilscli
from test.operate.test_download_public import REPO, ARCHIVE, extracted_by_tarfile
from test.testings import dir_compare


@pytest.mark.unittest
class TestEntryDownloadPublic:
    def test_download_archive_as_directory(self):
        with isolated_directory():
            extracted_by_tarfile('expected')
            result = simulate_entry(hfutilscli, ['hfutils', 'download', '-r', REPO, '-a', ARCHIVE, '-o', 'download_dir'])
            assert result.exitcode == 0, (f'Exitcode: {result.exitcode!r}\nError: {result.error!r}\n'
                                          f'========= Stdout =========\n{result.stdout}\n'
                                          f'========= Stderr =========\n{result.stderr}\n')
            dir_compare('expected', 'download_dir')

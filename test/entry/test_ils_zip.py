"""``hfutils ils`` on zip archives of a (recorded) repository, see ``test/index/zip_repo.py``."""
import click
import pytest
from hbutils.testing import simulate_entry

from hfutils.entry import hfutilscli
from hfutils.index import NotAZipError, zip_get_index
from test.index.zip.repo import zip_repo  # noqa: F401
from test.testings import get_testfile


def _run(*args):
    result = simulate_entry(hfutilscli, ['hfutils', 'ils', *args])
    return result.exitcode, click.unstyle(result.stdout).splitlines(keepends=False), click.unstyle(result.stderr)


def _ils(repo, *args):
    code, lines, err = _run('-r', repo, *args)
    assert code == 0, f'exit code {code}\nstderr: {err}\nstdout: {lines}'
    return lines


@pytest.mark.unittest
class TestEntryIlsZip:
    def test_list_by_offset_name_and_size(self, zip_repo):
        local = zip_get_index(get_testfile('zipfiles', 'methods-bzip2.zip'))['files']
        by_offset = [p for p, _ in sorted(local.items(), key=lambda x: (x[1]['offset'], x[0]))]
        assert _ils(zip_repo, '-a', 'zips/methods-bzip2.zip') == by_offset
        assert _ils(zip_repo, '-a', 'zips/methods-bzip2.zip', '-o', 'desc') == by_offset[::-1]
        assert _ils(zip_repo, '-a', 'zips/methods-bzip2.zip', '-s', 'name') == sorted(local)
        assert _ils(zip_repo, '-a', 'zips/methods-bzip2.zip', '-s', 'size', '-o', 'desc') == \
               [p for p, _ in sorted(local.items(), key=lambda x: (x[1]['size'], x[1]['offset'], x[0]), reverse=True)]

    def test_detailed_has_offset_name_size_and_crc(self, zip_repo):
        local = zip_get_index(get_testfile('zipfiles', 'methods-bzip2.zip'))['files']
        lines = _ils(zip_repo, '-a', 'zips/methods-bzip2.zip', '-l')
        assert len(lines) == len(local)
        for line in lines:
            offset, rest = line.split(' | ', 1)
            name = next(n for n in local if n in rest)
            assert int(offset) == local[name]['offset']
            assert rest.split()[-1] == f'{local[name]["crc32"]:08x}'

    def test_information(self, zip_repo):
        lines = _ils(zip_repo, '-a', 'zips/methods-bzip2.zip', '-I')
        text = '\n'.join(lines)
        assert 'Format: zip' in text
        assert 'Methods: bzip2 (4)' in text
        assert 'Encrypted: no' in text
        assert 'Files: 4 files' in text
        assert 'Status: Up-To-Date' in text
        assert 'Native Hash' not in text  # a zip has no index file to hash

    def test_information_of_a_single_file_archive_and_of_an_encrypted_one(self, zip_repo):
        text = '\n'.join(_ils(zip_repo, '-a', 'zips/thirdparty-ziprs-implode.zip', '-I'))
        assert 'Files: 1 file' in text and 'implode (1)' in text
        assert 'Encrypted: yes' in '\n'.join(_ils(zip_repo, '-a', 'zips/crypto-zipcrypto.zip', '-I'))

    def test_split_volumes(self, zip_repo):
        text = '\n'.join(_ils(zip_repo, '-a', 'split/split-7z.zip.002', '-I'))
        assert 'Volumes: 3' in text and 'split/split-7z.zip.001' in text
        assert 'blob.bin' in _ils(zip_repo, '-a', 'split/split-infozip.z01')

    def test_encoding(self, zip_repo):
        assert sorted(_ils(zip_repo, '-a', 'zips/names-gbk.zip', '--encoding', 'gbk')) == ['图片/猫猫.txt', '测试资料.txt']
        assert 'Names Encoding: shift_jis' in '\n'.join(_ils(zip_repo, '-a', 'zips/names-shiftjis.zip', '-I'))

    def test_a_zip_under_any_name(self, zip_repo):
        assert 'hello.txt' in _ils(zip_repo, '-a', 'odd/archive.jar')
        assert 'hello.txt' in _ils(zip_repo, '-a', 'odd/noext')
        assert 'hello.txt' in _ils(zip_repo, '-a', 'odd/noext', '-f', 'zip')

    @pytest.mark.parametrize('archive,text', [
        ('notzip/page.zip', 'HTML'), ('notzip/pointer.zip', 'Git LFS pointer'), ('notzip/empty.zip', 'empty'),
        ('notzip/image.zip', 'PNG'), ('split/split-7z.zip.004', 'no such archive'),
    ])
    def test_errors_are_messages_not_tracebacks(self, zip_repo, archive, text):
        code, lines, err = _run('-r', zip_repo, '-a', archive)
        assert code == 1
        assert text in err + '\n'.join(lines)

    def test_zip_has_no_index_options(self, zip_repo):
        code, _, err = _run('-r', zip_repo, '-a', 'zips/methods-bzip2.zip', '-f', 'zip', '--idx_repository', 'x/y')
        assert code == 2 and 'no index file' in err


@pytest.mark.unittest
class TestEntryIlsFormatChoice:
    """Which way ``auto`` goes, without a network."""

    def test_a_tar_with_another_name_goes_the_tar_way(self, monkeypatch):
        from hfutils.entry import ils

        def not_zip(**_):
            raise NotAZipError('it is a tar', detected='tar')

        monkeypatch.setattr(ils, 'hf_zip_get_index', not_zip)
        monkeypatch.setattr(ils, 'hf_tar_get_index', lambda **_: {'files': {'a.txt': {'offset': 512, 'size': 3, 'sha256': 'x'}}})
        code, lines, _ = _run('-r', 'o/r', '-a', 'weird.dat')
        assert code == 0 and lines == ['a.txt']

    def test_a_tar_name_or_an_index_never_asks_for_a_zip(self, monkeypatch):
        from hfutils.entry import ils

        def no_zip(**_):
            raise AssertionError('must not be asked')

        monkeypatch.setattr(ils, 'hf_zip_get_index', no_zip)
        monkeypatch.setattr(ils, 'hf_tar_get_index', lambda **_: {'files': {'a.txt': {'offset': 512, 'size': 3, 'sha256': 'x'}}})
        assert _run('-r', 'o/r', '-a', 'data.tar')[0] == 0
        assert _run('-r', 'o/r', '-a', 'data.zip', '-i', 'data.json')[0] == 0
        assert _run('-r', 'o/r', '-a', 'data.bin', '--idx_repository', 'o/idx')[0] == 0
        assert _run('-r', 'o/r', '-a', 'data.tar.gz')[0] == 0

    def test_the_comment_of_the_archive_is_shown(self, monkeypatch):
        from hfutils.entry import ils
        info = {'files': {'a.txt': {'offset': 0, 'size': 3, 'crc32': 0xabcdef, 'method_name': 'stored'}}, 'archive_size': 100,
                'volumes': ['x.zip'], 'encoding': 'utf-8', 'encrypted': False, 'comment': 'made for a test'}
        monkeypatch.setattr(ils, 'hf_zip_get_index', lambda **_: info)
        code, lines, _ = _run('-r', 'o/r', '-a', 'x.zip', '-I')
        assert code == 0 and 'Comment: made for a test' in '\n'.join(lines)
        info['comment'] = ''
        assert 'Comment' not in '\n'.join(_run('-r', 'o/r', '-a', 'x.zip', '-I')[1])

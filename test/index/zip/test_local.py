"""Reading zip archives from the local disk: every fixture against an independent extractor (7-Zip, Info-ZIP, Python 3.14's zipfile)
recorded in ``test/testfile/zipfiles/manifest.json``, the odd cases, the passwords, the volumes and what is not a zip."""
import hashlib
import io
import json
import os
import shutil
import struct
import tarfile
import zipfile

import pytest
from hbutils.testing import isolated_directory

from hfutils.index import (zip_get_index, zip_list_files, zip_file_exists, zip_file_info, zip_file_size, zip_file_read,
                           zip_file_write_bytes, zip_file_download, zip_cache_reset, NotAZipError, ZipVolumeError,
                           ZipPasswordRequiredError, ZipPasswordError, ZipUnsupportedError, ZipFormatError, ZipIndexError, ZipFetchError)
from hfutils.index.zip.directory import open_zip
from hfutils.index.zip.reader import ZipArchive
from hfutils.index.zip.source import FileSource
from test.testings import get_testfile

with open(get_testfile('zipfiles', 'manifest.json'), 'r', encoding='utf-8') as _f:
    MANIFEST = json.load(_f)

HELLO = b'hello from the zip fixture\n'
README = b'# Fixture\n\nNested markdown member.\n'


def fx(name):
    return get_testfile('zipfiles', name)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def need(module):
    pytest.importorskip(module)


# what a fixture needs that is not in the standard library
NEEDS = {
    'crypto-aes256.zip': 'cryptography', 'crypto-aes256-bzip2.zip': 'cryptography',
    'methods-deflate64.zip': 'inflate64',
}
PASSWORD = {n: 'secret' for n in MANIFEST if n.startswith('crypto-') and n != 'crypto-two-passwords.zip'}
LANG = {'names-cp866.zip': 'ru'}
FIRST_VOLUMES = {n for n in MANIFEST if n.endswith(('.z01', '.z02', '.zip.002', '.zip.003'))}


def _zstd_available():
    try:
        from compression import zstd  # noqa: F401
        return True
    except ImportError:
        try:
            import zstandard  # noqa: F401
            return True
        except ImportError:
            return False


@pytest.fixture(autouse=True)
def _fresh():
    zip_cache_reset()
    yield
    zip_cache_reset()


@pytest.mark.unittest
class TestZipAgainstOracles:
    """Every member of every fixture decodes to the bytes the oracle (7-Zip, unzip, Python 3.14) extracted."""

    @pytest.mark.parametrize('name', sorted(n for n, m in MANIFEST.items() if m.get('oracle')
                                            and n not in FIRST_VOLUMES and n != 'methods-ppmd.zip' and n != 'names-odd.zip'))
    def test_content_equals_oracle(self, name):
        if name in NEEDS:
            need(NEEDS[name])
        if name == 'methods-zstd.zip' and not _zstd_available():
            pytest.skip('zstd needs Python 3.14 or the zstandard package')
        spec = MANIFEST[name]
        got = []
        for path in zip_list_files(fx(name), lang=LANG.get(name, 'en')):
            data = zip_file_read(fx(name), path, password=PASSWORD.get(name), lang=LANG.get(name, 'en'))
            got.append([len(data), sha(data)])
            assert zip_file_size(fx(name), path, lang=LANG.get(name, 'en')) == len(data)
        assert sorted(got) == sorted(spec['digests'])

    @pytest.mark.parametrize('name', sorted(n for n, m in MANIFEST.items() if m.get('oracle') and n not in FIRST_VOLUMES
                                            and n.startswith(('methods-', 'split-', 'thirdparty-', 'prefix-', 'empty'))
                                            and n not in ('methods-ppmd.zip', 'methods-deflate64.zip', 'methods-zstd.zip')))
    def test_names_equal_oracle_when_it_can_tell(self, name):
        # the oracle reads names with a guess of its own, so only the archives whose names are plain UTF-8 are compared by name
        spec = MANIFEST[name]
        if name == 'thirdparty-libarchive-unicode-path.zip':
            pytest.skip('the oracle does not read the Unicode Path field')
        assert sorted(zip_list_files(fx(name))) == sorted(spec['members'])

    def test_two_passwords_against_stdlib(self):
        # the stdlib reads ZipCrypto too: it tells, member by member, which password opens it, and what is inside
        want = MANIFEST['crypto-zipcrypto.zip']['members']
        opened = {}
        with zipfile.ZipFile(fx('crypto-two-passwords.zip')) as zf:
            for info in zf.infolist():
                if info.is_dir():
                    continue
                for pw in ('alpha', 'beta'):
                    try:
                        data = zf.read(info, pwd=pw.encode())
                    except RuntimeError:
                        continue
                    opened[info.filename] = (pw, data)
                    break
        assert sorted(opened) == sorted(zip_list_files(fx('crypto-two-passwords.zip')))
        assert {pw for pw, _ in opened.values()} == {'alpha', 'beta'}  # both passwords are in use
        for path, (pw, data) in opened.items():
            assert sha(data) == want[path]['sha256']
            assert zip_file_read(fx('crypto-two-passwords.zip'), path, password=pw) == data
            other = 'beta' if pw == 'alpha' else 'alpha'
            with pytest.raises(ZipPasswordError):
                zip_file_read(fx('crypto-two-passwords.zip'), path, password=other)

    def test_every_fixture_has_an_oracle_or_a_reason(self):
        for name, spec in MANIFEST.items():
            assert spec.get('oracle') or spec.get('reason') or name in (
                'crypto-two-passwords.zip', 'thirdparty-ziprs-reduce.zip', 'zip64-missing-records.zip',
                'thirdparty-libarchive-encrypted-directory.zip', 'thirdparty-libarchive-strong-encryption.zip'), name


@pytest.mark.unittest
class TestZipContent:
    def test_fixed_members(self):
        assert zip_file_read(fx('methods-bzip2.zip'), 'hello.txt') == HELLO
        assert zip_file_read(fx('methods-lzma.zip'), 'docs/readme.md') == README
        assert zip_file_read(fx('crypto-partial.zip'), 'hello.txt') == HELLO

    def test_index(self):
        index = zip_get_index(fx('methods-bzip2.zip'))
        assert sorted(index['files']) == ['data/table.csv', 'docs/readme.md', 'hello.txt', 'images/noise.jpg']
        assert index['files']['hello.txt']['size'] == len(HELLO)
        assert index['files']['hello.txt']['method_name'] == 'bzip2'
        assert [os.path.basename(v) for v in index['volumes']] == ['methods-bzip2.zip']
        assert index['encrypted'] is False
        assert zip_file_info(fx('methods-bzip2.zip'), 'hello.txt')['crc32'] == index['files']['hello.txt']['crc32']

    def test_exists_and_missing(self):
        assert zip_file_exists(fx('methods-bzip2.zip'), 'hello.txt')
        assert not zip_file_exists(fx('methods-bzip2.zip'), 'docs')  # a directory is not a file
        assert not zip_file_exists(fx('methods-bzip2.zip'), 'nope.txt')
        with pytest.raises(FileNotFoundError):
            zip_file_read(fx('methods-bzip2.zip'), 'nope.txt')
        with pytest.raises(FileNotFoundError):
            zip_file_size(fx('methods-bzip2.zip'), 'nope.txt')

    def test_empty_archive(self):
        assert zip_list_files(fx('empty.zip')) == []

    def test_limit(self):
        full = zip_file_read(fx('methods-lzma.zip'), 'images/noise.jpg')
        for n in (0, 1, 100, len(full) - 1, len(full), len(full) + 50):
            assert zip_file_read(fx('methods-lzma.zip'), 'images/noise.jpg', limit=n) == full[:n]

    def test_write_bytes_and_download(self):
        buf = io.BytesIO()
        assert zip_file_write_bytes(fx('methods-bzip2.zip'), 'hello.txt', buf) == len(HELLO)
        assert buf.getvalue() == HELLO
        buf = io.BytesIO()
        assert zip_file_write_bytes(fx('methods-bzip2.zip'), 'hello.txt', buf, limit=5) == 5
        with isolated_directory():
            zip_file_download(fx('methods-bzip2.zip'), 'docs/readme.md', 'a/b/out.md')
            with open('a/b/out.md', 'rb') as f:
                assert f.read() == README
            assert os.listdir('a/b') == ['out.md']

    def test_failed_download_leaves_nothing(self):
        with isolated_directory():
            with pytest.raises(ZipPasswordRequiredError):
                zip_file_download(fx('crypto-zipcrypto.zip'), 'hello.txt', 'out.txt')
            assert os.listdir('.') == []

    def test_unsupported_method(self):
        with pytest.raises(ZipUnsupportedError) as ei:
            zip_file_read(fx('methods-ppmd.zip'), 'data/table.csv')
        assert ei.value.method == 98 and ei.value.kind == 'unsupported'
        assert zip_list_files(fx('methods-ppmd.zip')) == ['data/table.csv']  # listing still works

    @pytest.mark.parametrize('name,path,method,modules', [
        ('methods-deflate64.zip', 'data/table.csv', 9, ['inflate64']),
        ('methods-zstd.zip', 'hello.txt', 93, ['compression.zstd', 'zstandard']),
    ])
    def test_missing_optional_package_is_explained(self, monkeypatch, name, path, method, modules):
        import sys
        for module in modules:
            monkeypatch.setitem(sys.modules, module, None)  # importing it raises ImportError
        if 'compression.zstd' in modules and 'compression' in sys.modules:  # Python 3.14: `from compression import zstd` finds it here
            monkeypatch.delattr(sys.modules['compression'], 'zstd', raising=False)
        with pytest.raises(ZipUnsupportedError) as ei:
            zip_file_read(fx(name), path)
        assert ei.value.method == method and ei.value.kind == 'unsupported'
        assert zip_file_exists(fx(name), path)  # listing never needs them

    def test_strong_encryption(self):
        assert sorted(zip_list_files(fx('thirdparty-libarchive-strong-encryption.zip'))) == ['bar.txt', 'foo.txt']
        with pytest.raises(ZipUnsupportedError, match='strong encryption'):
            zip_file_read(fx('thirdparty-libarchive-strong-encryption.zip'), 'foo.txt', password='x')

    def test_encrypted_directory(self):
        with pytest.raises(ZipUnsupportedError, match='central directory'):
            zip_list_files(fx('thirdparty-libarchive-encrypted-directory.zip'))

    def test_legacy_methods(self):
        for name, path in (('thirdparty-ziprs-shrink.zip', 'FIRST.TXT'), ('thirdparty-ziprs-reduce.zip', 'first.txt'),
                           ('thirdparty-ziprs-implode.zip', 'first.txt')):
            data = zip_file_read(fx(name), path)
            e = zip_get_index(fx(name))['files'][path]
            assert len(data) == e['size'] == 1092

    def test_zip64_records_missing(self):
        index = zip_get_index(fx('zip64-missing-records.zip'))
        assert sorted(index['files']) == ['docs/readme.md', 'hello.txt']
        assert index['notes'] and 'ZIP64' in index['notes'][0]
        assert zip_file_read(fx('zip64-missing-records.zip'), 'hello.txt') == HELLO

    def test_prefix_data_is_skipped(self):
        assert zip_file_read(fx('prefix-sfx.zip'), 'hello.txt') == HELLO

    def test_lzma_without_end_marker_is_cut_at_the_size(self):
        data = zip_file_read(fx('thirdparty-libarchive-lzma-sized.zipx'), 'vimrc')
        assert len(data) == zip_file_size(fx('thirdparty-libarchive-lzma-sized.zipx'), 'vimrc')


@pytest.mark.unittest
class TestZipNames:
    def test_odd_names(self):
        assert sorted(zip_list_files(fx('names-odd.zip'))) == ['a/b/c.txt', 'abs/path.txt', 'dup.txt', 'empty.txt', 'escape.txt']
        assert zip_file_read(fx('names-odd.zip'), 'dup.txt') == b'first\n'  # the first of duplicates wins
        assert zip_file_read(fx('names-odd.zip'), 'escape.txt') == b'traversal\n'
        assert zip_file_read(fx('names-odd.zip'), 'empty.txt') == b''

    def test_shiftjis_and_gbk_are_guessed(self):
        assert sorted(zip_list_files(fx('names-shiftjis.zip'))) == ['テスト資料.txt', '画像/猫.txt']
        assert zip_get_index(fx('names-shiftjis.zip'))['encoding'] == 'shift_jis'
        assert sorted(zip_list_files(fx('names-gbk.zip'))) == ['图片/猫猫.txt', '测试资料.txt']
        assert zip_get_index(fx('names-gbk.zip'))['encoding'] == 'gbk'

    def test_cp866_needs_the_language_or_the_encoding(self):
        assert zip_list_files(fx('names-cp866.zip'), lang='ru') == ['Привет/мир.txt']
        assert zip_list_files(fx('names-cp866.zip'), encoding='ibm866') == ['Привет/мир.txt']
        assert zip_list_files(fx('names-cp866.zip'))[0] != 'Привет/мир.txt'  # CP437 by default

    def test_unknown_encoding(self):
        with pytest.raises(ValueError):
            zip_list_files(fx('names-gbk.zip'), encoding='nope')

    def test_unicode_path_field(self):
        assert 'File 4 - å.txt' in zip_list_files(fx('thirdparty-libarchive-unicode-path.zip'))


@pytest.mark.unittest
class TestZipPasswords:
    def test_required_wrong_and_right(self):
        for name in ('crypto-zipcrypto.zip', 'crypto-zipcrypto-stream.zip', 'crypto-aes256.zip'):
            if 'aes' in name:
                need('cryptography')
            with pytest.raises(ZipPasswordRequiredError) as ei:
                zip_file_read(fx(name), 'hello.txt')
            assert ei.value.kind == 'password'
            with pytest.raises(ZipPasswordError):
                zip_file_read(fx(name), 'hello.txt', password='not-it')
            assert zip_file_read(fx(name), 'hello.txt', password='secret') == HELLO
            assert zip_file_read(fx(name), 'hello.txt', password=['x', b'secret']) == HELLO

    def test_listing_needs_no_password(self):
        assert zip_get_index(fx('crypto-zipcrypto.zip'))['encrypted'] is True
        assert len(zip_list_files(fx('crypto-zipcrypto.zip'))) == 4

    def test_plain_members_are_readable_without_a_password(self):
        files = zip_get_index(fx('crypto-partial.zip'))['files']
        plain = [n for n, i in files.items() if not i['encrypted']]
        locked = [n for n, i in files.items() if i['encrypted']]
        assert len(plain) == len(locked) == 1
        assert zip_file_read(fx('crypto-partial.zip'), plain[0]) in (HELLO, README)
        with pytest.raises(ZipPasswordRequiredError):
            zip_file_read(fx('crypto-partial.zip'), locked[0])
        assert zip_file_read(fx('crypto-partial.zip'), locked[0], password='secret') in (HELLO, README)

    def test_two_passwords_remembered(self):
        archive = ZipArchive(open_zip('crypto-two-passwords.zip', lambda n: FileSource(fx(n)) if os.path.exists(fx(n)) else None))
        want = MANIFEST['crypto-zipcrypto.zip']['members']
        assert not archive.unlock('wrong')
        assert archive.passwords == []
        # every member is encrypted with one of the two; the archive keeps the ones that worked, most recent first
        for path in archive.paths():
            assert sha(archive.read(path, password=['alpha', 'beta'])) == want[path]['sha256']
        assert sorted(archive.passwords) == [b'alpha', b'beta']
        for path in archive.paths():
            assert sha(archive.read(path)) == want[path]['sha256']  # no password given: the remembered ones are enough

    def test_unlock(self):
        archive = ZipArchive(open_zip('crypto-zipcrypto.zip', lambda n: FileSource(fx(n)) if os.path.exists(fx(n)) else None))
        assert archive.unlock('secret') and archive.passwords == [b'secret']
        assert archive.read('hello.txt') == HELLO  # remembered
        plain = ZipArchive(open_zip('methods-bzip2.zip', lambda n: FileSource(fx(n)) if os.path.exists(fx(n)) else None))
        assert plain.unlock('anything')  # nothing is encrypted: nothing to refuse

    def test_aes_over_bzip2(self):
        need('cryptography')
        assert zip_file_read(fx('crypto-aes256-bzip2.zip'), 'hello.txt', password='secret') == HELLO

    def test_aes_without_the_package_says_so(self, monkeypatch):
        import builtins
        real = builtins.__import__

        def fake(name, *a, **k):
            if name.startswith('cryptography'):
                raise ImportError(name)
            return real(name, *a, **k)

        monkeypatch.setattr(builtins, '__import__', fake)
        with pytest.raises(ZipUnsupportedError, match='cryptography'):
            zip_file_read(fx('crypto-aes256.zip'), 'hello.txt', password='secret')

    def test_aes_tamper_is_detected(self):
        need('cryptography')
        with isolated_directory():
            data = bytearray(open(fx('crypto-aes256.zip'), 'rb').read())
            index = zip_get_index(fx('crypto-aes256.zip'))['files']['hello.txt']
            name_len, extra_len = struct.unpack_from('<HH', data, index['offset'] + 26)
            data[index['offset'] + 30 + name_len + extra_len + 16 + 2 + 1] ^= 0x55  # a byte of the ciphertext, after salt + verifier
            with open('t.zip', 'wb') as f:
                f.write(data)
            with pytest.raises(ZipFormatError, match='authentication'):
                zip_file_read('t.zip', 'hello.txt', password='secret')


@pytest.mark.unittest
class TestZipVolumes:
    @pytest.mark.parametrize('name', ['split-7z.zip.001', 'split-7z.zip.002', 'split-7z.zip.003', 'split-infozip.z01',
                                      'split-infozip.z02', 'split-infozip.zip'])
    def test_any_volume_opens_the_whole_set(self, name):
        spec = MANIFEST['split-7z.zip.001' if 'zip.0' in name else 'split-infozip.zip']
        files = zip_list_files(fx(name))
        assert sorted(files) == sorted(spec['members'])
        for path in files:
            data = zip_file_read(fx(name), path)
            assert sha(data) == spec['members'][path]['sha256'] and len(data) == spec['members'][path]['size']

    def test_volume_list(self):
        names = lambda name: [os.path.basename(v) for v in zip_get_index(fx(name))['volumes']]  # noqa: E731
        assert names('split-7z.zip.002') == ['split-7z.zip.001', 'split-7z.zip.002', 'split-7z.zip.003']
        assert names('split-infozip.z01') == ['split-infozip.z01', 'split-infozip.z02', 'split-infozip.zip']

    def test_member_across_volumes(self):
        # blob.bin is 180000 bytes spread over three volumes
        for name in ('split-7z.zip.001', 'split-infozip.zip'):
            index = zip_get_index(fx(name))['files']['blob.bin']
            assert index['size'] == 180000
            assert len(zip_file_read(fx(name), 'blob.bin')) == 180000

    @pytest.mark.parametrize('present,asked,missing', [
        (['split-7z.zip.001', 'split-7z.zip.003'], 'split-7z.zip.003', 'split-7z.zip.002'),
        (['split-7z.zip.001', 'split-7z.zip.002'], 'split-7z.zip.001', 'split-7z.zip.003'),
        (['split-7z.zip.002', 'split-7z.zip.003'], 'split-7z.zip.002', 'split-7z.zip.001'),
        (['split-infozip.z01', 'split-infozip.zip'], 'split-infozip.zip', 'split-infozip.z02'),
        (['split-infozip.z01', 'split-infozip.z02'], 'split-infozip.z01', 'split-infozip.zip'),
    ])
    def test_a_missing_volume_is_named(self, present, asked, missing):
        with isolated_directory():
            for name in present:
                shutil.copy(fx(name), name)
            with pytest.raises(ZipVolumeError) as ei:
                zip_list_files(asked)
            assert ei.value.kind == 'format'
            assert missing in str(ei.value) and ei.value.missing == [missing]


@pytest.mark.unittest
class TestZipNotAZip:
    def _check(self, data, detected, name='thing.zip'):
        with isolated_directory():
            with open(name, 'wb') as f:
                f.write(data)
            with pytest.raises(NotAZipError) as ei:
                zip_list_files(name)
            assert ei.value.detected == detected
            assert ei.value.kind == 'format'
            assert isinstance(ei.value, ValueError) and isinstance(ei.value, ZipIndexError)

    def test_samples(self):
        buf = io.BytesIO()
        with tarfile.open(fileobj=buf, mode='w') as tf:
            info = tarfile.TarInfo('a.txt')
            info.size = 3
            tf.addfile(info, io.BytesIO(b'abc'))
        self._check(buf.getvalue(), 'tar')
        self._check(b'\x1f\x8b\x08\x00' + b'\x00' * 100, 'gzip')
        self._check(b'BZh9' + b'\x00' * 100, 'bzip2')
        self._check(b'\x89PNG\r\n\x1a\n' + b'\x00' * 100, 'png')
        self._check(b'\xff\xd8\xff\xe0' + b'\x00' * 100, 'jpeg')
        self._check(b'%PDF-1.7\n' + b'x' * 100, 'pdf')
        self._check(b'7z\xbc\xaf\x27\x1c' + b'\x00' * 100, '7z')
        self._check(b'Rar!\x1a\x07\x00' + b'\x00' * 100, 'rar')
        self._check(b'version https://git-lfs.github.com/spec/v1\noid sha256:' + b'a' * 64 + b'\nsize 12345\n', 'git-lfs-pointer')
        self._check(b'<!DOCTYPE html><html><body>Not found</body></html>', 'html')
        self._check(b'{"error": "Entry not found"}', 'json')
        self._check(b'', 'empty')
        self._check(os.urandom(2000), None)

    def test_truncated_zip_and_a_volume_part(self):
        with open(fx('methods-bzip2.zip'), 'rb') as f:
            data = f.read()
        self._check(data[:200], 'truncated-zip')
        self._check(data[:200], 'truncated-zip', name='thing.bin')

    def test_a_tar_named_zip_and_the_reverse(self):
        with isolated_directory():
            shutil.copy(fx('methods-bzip2.zip'), 'real.tar')  # a zip named .tar is still a zip
            assert 'hello.txt' in zip_list_files('real.tar')

    @pytest.mark.parametrize('name', ['a.jar', 'a.docx', 'a.xlsx', 'a.whl', 'a.epub', 'a.cbz', 'a.npz', 'a.bin', 'a', 'a.dat.tmp',
                                      'A.ZIP', 'a.zipx', 'a.000', 'a.7z'])
    def test_any_name_is_a_zip_if_it_is_one(self, name):
        with isolated_directory():
            shutil.copy(fx('methods-bzip2.zip'), name)
            assert zip_file_read(name, 'hello.txt') == HELLO

    def test_not_found(self):
        with pytest.raises(FileNotFoundError):
            zip_list_files('does-not-exist.zip')
        with pytest.raises(FileNotFoundError):
            zip_list_files(fx('split-7z.zip.004'))  # a volume number that is not there, in a set that is complete
        with pytest.raises(ZipFetchError) as ei:
            zip_list_files('does-not-exist.zip')
        assert ei.value.kind == 'fetch' and ei.value.status == 404


@pytest.mark.unittest
class TestZipStdlibRoundTrip:
    """Archives written by Python's zipfile (ZIP64 included) are read back to the same bytes."""

    @pytest.mark.parametrize('compression', [zipfile.ZIP_STORED, zipfile.ZIP_DEFLATED, zipfile.ZIP_BZIP2, zipfile.ZIP_LZMA])
    @pytest.mark.parametrize('force_zip64', [False, True])
    def test_round_trip(self, compression, force_zip64):
        files = {'a.txt': b'a' * 10, 'dir/b.bin': os.urandom(70000), 'dir/sub/c.txt': (b'line\n' * 5000), 'empty': b''}
        with isolated_directory():
            with zipfile.ZipFile('t.zip', 'w', compression) as zf:
                for name, data in files.items():
                    with zf.open(name, 'w', force_zip64=force_zip64) as w:
                        w.write(data)
            assert sorted(zip_list_files('t.zip')) == sorted(files)
            for name, data in files.items():
                assert zip_file_read('t.zip', name) == data

    def test_zip64_end_records_are_read(self):
        with isolated_directory():
            with zipfile.ZipFile('t.zip', 'w') as zf:
                zf.writestr(zipfile.ZipInfo('a.txt'), b'x' * 100)
                zf.writestr('b.txt', b'y')
            data = bytearray(open('t.zip', 'rb').read())
            eocd = data.rfind(b'PK\x05\x06')
            cd_size, cd_off = struct.unpack_from('<II', data, eocd + 12)
            z64 = struct.pack('<4sQHHIIQQQQ', b'PK\x06\x06', 44, 45, 45, 0, 0, 2, 2, cd_size, cd_off)
            loc = struct.pack('<4sIQI', b'PK\x06\x07', 0, eocd, 1)
            saturated_end = b'PK\x05\x06' + struct.pack('<HHHHIIH', 0xffff, 0xffff, 0xffff, 0xffff, 0xffffffff, 0xffffffff, 0)
            patched = bytes(data[:eocd]) + z64 + loc + saturated_end
            with open('z64.zip', 'wb') as f:
                f.write(patched)
            assert sorted(zip_list_files('z64.zip')) == ['a.txt', 'b.txt']
            assert zip_file_read('z64.zip', 'a.txt') == b'x' * 100

    def test_data_descriptors(self):
        class Unseekable(io.RawIOBase):
            def __init__(self):
                self.buf = io.BytesIO()

            def writable(self):
                return True

            def write(self, b):
                return self.buf.write(b)

        sink = Unseekable()
        with zipfile.ZipFile(sink, 'w', zipfile.ZIP_DEFLATED) as zf:
            zf.writestr('s.txt', b'streamed' * 1000)
        with isolated_directory():
            with open('t.zip', 'wb') as f:
                f.write(sink.buf.getvalue())
            assert zip_file_read('t.zip', 's.txt') == b'streamed' * 1000

    def test_damaged_data_is_reported(self):
        with isolated_directory():
            with zipfile.ZipFile('t.zip', 'w', zipfile.ZIP_STORED) as zf:
                zf.writestr('a.txt', b'hello world')
            data = bytearray(open('t.zip', 'rb').read())
            data[data.index(b'hello') + 1] ^= 0xff
            with open('t.zip', 'wb') as f:
                f.write(data)
            with pytest.raises(ZipFormatError, match='CRC'):
                zip_file_read('t.zip', 'a.txt')

    def test_a_directory_with_a_comment_and_trailing_zeros(self):
        with isolated_directory():
            with zipfile.ZipFile('t.zip', 'w') as zf:
                zf.writestr('a.txt', b'x')
                zf.comment = b'a comment that looks like PK\x05\x06 but is not a record'
            assert zip_list_files('t.zip') == ['a.txt']


@pytest.mark.unittest
class TestZipCaches:
    def test_cache_notices_a_changed_file(self):
        with isolated_directory():
            with zipfile.ZipFile('t.zip', 'w') as zf:
                zf.writestr('a.txt', b'1')
            assert zip_list_files('t.zip') == ['a.txt']
            with zipfile.ZipFile('t.zip', 'w') as zf:
                zf.writestr('a.txt', b'1')
                zf.writestr('b.txt', b'22')
            assert sorted(zip_list_files('t.zip')) == ['a.txt', 'b.txt']

    def test_remembered_passwords_are_not_shared_between_calls(self):
        assert zip_file_read(fx('crypto-zipcrypto.zip'), 'hello.txt', password='secret') == HELLO
        with pytest.raises(ZipPasswordRequiredError):
            zip_file_read(fx('crypto-zipcrypto.zip'), 'hello.txt')

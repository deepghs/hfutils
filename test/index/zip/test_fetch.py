"""The remote zip functions against a real (recorded) repository of the Hub: Range requests, redirects to the CDN, LFS, split
volumes, and the errors. The archives are the fixtures of ``test/testfile/zipfiles`` (see ``zip_repo``); what they must contain is
what an independent extractor said (``manifest.json``) and what the local functions return."""
import hashlib
import io
import json
import os

import pytest
from hbutils.testing import isolated_directory

from hfutils.index import (hf_zip_get_index, hf_zip_list_files, hf_zip_file_exists, hf_zip_file_info, hf_zip_file_size,
                           hf_zip_file_read, hf_zip_file_write_bytes, hf_zip_file_download, hf_zip_cache_reset, zip_get_index,
                           NotAZipError, ZipVolumeError, ZipPasswordRequiredError, ZipPasswordError,
                           ZipUnsupportedError, ZipFetchError)
from hfutils.index.zip.source import HfSource
from test.index.zip.repo import zip_repo, BIG_MEMBER, big_payload  # noqa: F401
from test.testings import get_testfile

with open(get_testfile('zipfiles', 'manifest.json'), 'r', encoding='utf-8') as _f:
    MANIFEST = json.load(_f)

HELLO = b'hello from the zip fixture\n'


def fx(name):
    return get_testfile('zipfiles', name)


def sha(data):
    return hashlib.sha256(data).hexdigest()


@pytest.fixture(autouse=True)
def _fresh():
    hf_zip_cache_reset()
    yield
    hf_zip_cache_reset()


@pytest.fixture()
def count_requests(monkeypatch):
    calls = []
    real = HfSource.fetch

    def fetch(self, start, length):
        calls.append((self.path, start, length))
        return real(self, start, length)

    monkeypatch.setattr(HfSource, 'fetch', fetch)
    return calls


@pytest.mark.unittest
class TestZipFetch:
    def test_every_archive_reads_like_the_local_one(self, zip_repo):
        for name in ('methods-bzip2.zip', 'methods-lzma.zip', 'names-shiftjis.zip', 'names-gbk.zip', 'names-odd.zip',
                     'prefix-sfx.zip', 'zip64-missing-records.zip', 'empty.zip', 'thirdparty-ziprs-implode.zip',
                     'thirdparty-libarchive-xz.zipx', 'crypto-zipcrypto.zip', 'thirdparty-libarchive-unicode-path.zip'):
            remote = hf_zip_get_index(zip_repo, f'zips/{name}')
            local = zip_get_index(fx(name))
            assert remote['files'].keys() == local['files'].keys(), name
            for path, info in remote['files'].items():
                for key in ('size', 'crc32', 'method', 'encrypted', 'compressed_size', 'offset'):
                    assert info[key] == local['files'][path][key], (name, path, key)
            assert remote['encoding'] == local['encoding']
            assert hf_zip_list_files(zip_repo, f'zips/{name}') == list(local['files'])
            spec = MANIFEST[name]
            if spec.get('oracle') and not name.startswith(('names-', 'thirdparty-libarchive-unicode')):
                got = []
                for path in remote['files']:
                    data = hf_zip_file_read(zip_repo, f'zips/{name}', path, password='secret')
                    got.append([len(data), sha(data)])
                assert sorted(got) == sorted(spec['digests']), name

    def test_methods_that_cannot_be_decoded_are_listed_and_named(self, zip_repo):
        # what decoding needs (inflate64, zstandard, cryptography) is independent of where the bytes come from and is tested on the
        # local files; here the same requests must be made in every environment, so nothing depends on an optional package
        for name in ('methods-deflate64.zip', 'methods-zstd.zip', 'methods-ppmd.zip', 'crypto-aes256.zip'):
            assert hf_zip_list_files(zip_repo, f'zips/{name}') == list(zip_get_index(fx(name))['files'])
        with pytest.raises(ZipUnsupportedError) as ei:
            hf_zip_file_read(zip_repo, 'zips/methods-ppmd.zip', 'data/table.csv')
        assert ei.value.method == 98

    def test_passwords(self, zip_repo):
        with pytest.raises(ZipPasswordRequiredError):
            hf_zip_file_read(zip_repo, 'zips/crypto-zipcrypto.zip', 'hello.txt')
        with pytest.raises(ZipPasswordError):
            hf_zip_file_read(zip_repo, 'zips/crypto-zipcrypto.zip', 'hello.txt', password='nope')
        assert hf_zip_file_read(zip_repo, 'zips/crypto-zipcrypto.zip', 'hello.txt', password='secret') == HELLO
        assert hf_zip_file_read(zip_repo, 'zips/crypto-two-passwords.zip', 'hello.txt', password=['alpha', 'beta']) == HELLO

    def test_encoding_and_lang(self, zip_repo):
        assert sorted(hf_zip_list_files(zip_repo, 'zips/names-shiftjis.zip')) == ['テスト資料.txt', '画像/猫.txt']
        assert sorted(hf_zip_list_files(zip_repo, 'zips/names-gbk.zip', encoding='gbk')) == ['图片/猫猫.txt', '测试资料.txt']

    def test_any_extension_and_none(self, zip_repo):
        for path in ('odd/archive.jar', 'odd/noext'):
            assert hf_zip_file_read(zip_repo, path, 'hello.txt') == HELLO

    def test_request_counts(self, zip_repo, count_requests):
        assert hf_zip_file_read(zip_repo, 'zips/methods-bzip2.zip', 'hello.txt') == HELLO
        assert len(count_requests) == 2  # the tail (the whole small archive: directory included), then the member
        assert hf_zip_file_read(zip_repo, 'zips/methods-bzip2.zip', 'docs/readme.md').startswith(b'# Fixture')
        assert len(count_requests) == 3  # the directory is cached: one request for the member only
        assert hf_zip_file_exists(zip_repo, 'zips/methods-bzip2.zip', 'hello.txt')
        assert hf_zip_file_size(zip_repo, 'zips/methods-bzip2.zip', 'hello.txt') == len(HELLO)
        assert hf_zip_file_info(zip_repo, 'zips/methods-bzip2.zip', 'hello.txt')['method_name'] == 'bzip2'
        assert len(count_requests) == 3

    def test_split_sets_and_gaps(self, zip_repo):
        for asked, spec_name in (('split/split-7z.zip.001', 'split-7z.zip.001'), ('split/split-7z.zip.002', 'split-7z.zip.001'),
                                 ('split/split-7z.zip.003', 'split-7z.zip.001'), ('split/split-infozip.z01', 'split-infozip.zip'),
                                 ('split/split-infozip.z02', 'split-infozip.zip'), ('split/split-infozip.zip', 'split-infozip.zip')):
            spec = MANIFEST[spec_name]['members']
            index = hf_zip_get_index(zip_repo, asked)
            assert len(index['volumes']) == 3
            assert sorted(index['files']) == sorted(spec)
            for path, want in spec.items():
                data = hf_zip_file_read(zip_repo, asked, path)
                assert len(data) == want['size'] and sha(data) == want['sha256'], (asked, path)
        with pytest.raises(ZipVolumeError) as ei:
            hf_zip_list_files(zip_repo, 'gap/split-7z.zip.003')
        assert ei.value.missing == ['gap/split-7z.zip.002'] and 'gap/split-7z.zip.002' in str(ei.value)
        with pytest.raises(ZipVolumeError):
            hf_zip_list_files(zip_repo, 'gap/split-7z.zip.001')
        with pytest.raises(FileNotFoundError):
            hf_zip_list_files(zip_repo, 'split/split-7z.zip.004')  # a volume that does not exist, in a set that does

    def test_not_a_zip(self, zip_repo):
        for path, detected in (('notzip/real.tar', 'tar'), ('notzip/pointer.zip', 'git-lfs-pointer'),
                               ('notzip/page.zip', 'html'), ('notzip/empty.zip', 'empty'), ('notzip/image.zip', 'png')):
            with pytest.raises(NotAZipError) as ei:
                hf_zip_get_index(zip_repo, path)
            assert ei.value.detected == detected, path
            assert ei.value.kind == 'format'

    def test_missing_archive_and_repository(self, zip_repo):
        with pytest.raises(FileNotFoundError):
            hf_zip_list_files(zip_repo, 'zips/not-there.zip')
        with pytest.raises(Exception) as ei:
            hf_zip_list_files('narugo1992/this-repository-does-not-exist-zip-test', 'a.zip')
        assert type(ei.value).__name__ in ('RepositoryNotFoundError', 'RemoteEntryNotFoundError', 'EntryNotFoundError',
                                           'HfHubHTTPError', 'ZipFetchError') or isinstance(ei.value, ZipFetchError)

    def test_a_big_member_comes_in_windows_and_a_head_costs_less(self, zip_repo, count_requests, monkeypatch):
        monkeypatch.setattr(HfSource, 'window', 128 * 1024)
        payload = big_payload()
        index = hf_zip_get_index(zip_repo, 'big/stored.zip')
        assert index['files'][BIG_MEMBER]['size'] == len(payload)
        count_requests.clear()
        assert hf_zip_file_read(zip_repo, 'big/stored.zip', BIG_MEMBER) == payload
        assert 5 <= len(count_requests) <= 8  # 768 KiB in windows of 128 KiB (the first one carries the local header)
        count_requests.clear()
        assert hf_zip_file_read(zip_repo, 'big/stored.zip', BIG_MEMBER, limit=1000) == payload[:1000]
        assert sum(length for _, _, length in count_requests) < 200 * 1024
        count_requests.clear()
        assert hf_zip_file_read(zip_repo, 'big/stored.zip', BIG_MEMBER, limit=300 * 1024) == payload[:300 * 1024]
        assert sum(length for _, _, length in count_requests) < len(payload)

    def test_write_bytes_and_download(self, zip_repo):
        buf = io.BytesIO()
        assert hf_zip_file_write_bytes(zip_repo, 'big/stored.zip', BIG_MEMBER, buf) == len(big_payload())
        assert buf.getvalue() == big_payload()
        with isolated_directory():
            hf_zip_file_download(zip_repo, 'zips/methods-bzip2.zip', 'docs/readme.md', 'x/y/readme.md')
            with open('x/y/readme.md', 'rb') as f:
                assert f.read() == b'# Fixture\n\nNested markdown member.\n'
            with pytest.raises(ZipPasswordRequiredError):
                hf_zip_file_download(zip_repo, 'zips/crypto-zipcrypto.zip', 'hello.txt', 'locked.txt')
            assert not os.path.exists('locked.txt') and os.listdir('.') == ['x']

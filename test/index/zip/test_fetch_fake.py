"""The logic of the remote zip functions (what is asked for, what is cached, whose token is used) without any network: the Hub is
replaced by a fake that serves the fixtures of ``test/testfile/zipfiles`` and counts the requests. What the real Hub does with those
requests is the business of ``test_fetch.py`` (recorded)."""
import os
from types import SimpleNamespace

import pytest

from hfutils.index import (hf_zip_get_index, hf_zip_list_files, hf_zip_file_read, hf_zip_file_exists, hf_zip_file_size,
                           hf_zip_cache_reset, ZipVolumeError, NotAZipError, ZipFetchError, ZipPasswordRequiredError)
from test.index.zip.fakehub import FakeHub
from test.testings import get_testfile

HELLO = b'hello from the zip fixture\n'


@pytest.fixture()
def hub(monkeypatch):
    hub = FakeHub({
        'a/methods-bzip2.zip': get_testfile('zipfiles', 'methods-bzip2.zip'),
        'a/crypto.zip': get_testfile('zipfiles', 'crypto-zipcrypto.zip'),
        'a/s.zip.001': get_testfile('zipfiles', 'split-7z.zip.001'),
        'a/s.zip.002': get_testfile('zipfiles', 'split-7z.zip.002'),
        'a/s.zip.003': get_testfile('zipfiles', 'split-7z.zip.003'),
        'a/d.z01': get_testfile('zipfiles', 'split-infozip.z01'),
        'a/d.z02': get_testfile('zipfiles', 'split-infozip.z02'),
        'a/d.zip': get_testfile('zipfiles', 'split-infozip.zip'),
        'a/gap.zip.001': get_testfile('zipfiles', 'split-7z.zip.001'),
        'a/gap.zip.003': get_testfile('zipfiles', 'split-7z.zip.003'),
        'a/notzip.bin': get_testfile('zipfiles', 'README.md'),
    })

    hub.install(monkeypatch)
    hf_zip_cache_reset()
    yield hub
    hf_zip_cache_reset()


@pytest.mark.unittest
class TestZipFetchFake:
    def test_the_directory_costs_one_request(self, hub):
        assert sorted(hf_zip_list_files('o/r', 'a/methods-bzip2.zip')) == \
               ['data/table.csv', 'docs/readme.md', 'hello.txt', 'images/noise.jpg']
        assert len(hub.fetches) == 1  # a small archive: the tail holds the whole directory
        assert hub.fetches[0][1] == 0

    def test_a_small_member_costs_one_more(self, hub):
        assert hf_zip_file_read('o/r', 'a/methods-bzip2.zip', 'hello.txt') == HELLO
        assert len(hub.fetches) == 2  # the tail, then the member together with its local header

    def test_the_second_read_needs_no_directory_request(self, hub):
        hf_zip_file_read('o/r', 'a/methods-bzip2.zip', 'hello.txt')
        before = len(hub.fetches)
        assert hf_zip_file_read('o/r', 'a/methods-bzip2.zip', 'docs/readme.md').startswith(b'# Fixture')
        assert len(hub.fetches) == before + 1
        assert hf_zip_file_exists('o/r', 'a/methods-bzip2.zip', 'hello.txt')
        assert hf_zip_file_size('o/r', 'a/methods-bzip2.zip', 'hello.txt') == len(HELLO)
        assert len(hub.fetches) == before + 1  # exists and size are answered by the directory
        assert len(hub.paths_info_calls) >= 3  # one revision check per call, never a download

    def test_a_changed_file_is_noticed(self, hub):
        hf_zip_list_files('o/r', 'a/methods-bzip2.zip')
        before = len(hub.fetches)
        hub.files['a/methods-bzip2.zip'] = get_testfile('zipfiles', 'methods-lzma.zip')  # same name, other size
        hf_zip_list_files('o/r', 'a/methods-bzip2.zip')
        assert len(hub.fetches) == before + 1  # the directory was read again

    def test_a_cached_directory_never_carries_the_token_of_the_first_caller(self, hub):
        hf_zip_file_read('o/r', 'a/methods-bzip2.zip', 'hello.txt', hf_token='token-of-A')
        hf_zip_file_read('o/r', 'a/methods-bzip2.zip', 'docs/readme.md', hf_token='token-of-B')
        tokens = [t for *_, t in hub.fetches]
        assert tokens[:2] == ['token-of-A', 'token-of-A']
        assert tokens[2:] == ['token-of-B']

    def test_passwords_are_not_cached(self, hub):
        assert hf_zip_file_read('o/r', 'a/crypto.zip', 'hello.txt', password='secret') == HELLO
        with pytest.raises(ZipPasswordRequiredError):
            hf_zip_file_read('o/r', 'a/crypto.zip', 'hello.txt')

    def test_limit_stops_early(self, hub):
        hf_zip_get_index('o/r', 'a/s.zip.001')
        hub.fetches.clear()
        data = hf_zip_file_read('o/r', 'a/s.zip.001', 'blob.bin', limit=100)
        assert len(data) == 100
        asked = sum(length for _, _, length, _ in hub.fetches)
        assert asked < 180000  # not the whole member (it spans three volumes)

    def test_split_volumes_are_looked_up_in_one_batch(self, hub):
        index = hf_zip_get_index('o/r', 'a/s.zip.002')
        assert index['volumes'] == ['a/s.zip.001', 'a/s.zip.002', 'a/s.zip.003']
        assert sorted(index['files']) == ['blob.bin', 'data/table.csv', 'docs/readme.md', 'hello.txt', 'images/noise.jpg']
        assert len(hub.paths_info_calls) <= 4  # the names around the asked one come in batches, not one request per volume

    def test_info_zip_disk_set_from_the_last_volume(self, hub):
        assert hf_zip_file_read('o/r', 'a/d.zip', 'hello.txt') == HELLO
        assert hf_zip_file_read('o/r', 'a/d.z01', 'docs/readme.md').startswith(b'# Fixture')

    def test_a_gap_in_the_volumes_is_named(self, hub):
        with pytest.raises(ZipVolumeError) as ei:
            hf_zip_list_files('o/r', 'a/gap.zip.003')
        assert ei.value.missing == ['a/gap.zip.002']

    def test_not_a_zip(self, hub):
        with pytest.raises(NotAZipError):
            hf_zip_list_files('o/r', 'a/notzip.bin')

    def test_missing_archive(self, hub):
        with pytest.raises(FileNotFoundError):
            hf_zip_list_files('o/r', 'a/nope.zip')

    def test_transport_failure_is_a_fetch_error(self, hub, monkeypatch):
        from hfutils.index.zip.source import HfSource as S

        def boom(self, start, length):
            raise ZipFetchError('connection reset', status=503)

        monkeypatch.setattr(S, 'fetch', boom)
        with pytest.raises(ZipFetchError) as ei:
            hf_zip_list_files('o/r', 'a/methods-bzip2.zip')
        assert ei.value.status == 503 and ei.value.kind == 'fetch'

    def test_a_failed_lookup_is_a_fetch_error_with_its_status(self, hub):
        class Boom(Exception):
            response = SimpleNamespace(status_code=500)

        hub.fail = Boom('server error')
        with pytest.raises(ZipFetchError) as ei:
            hf_zip_list_files('o/r', 'a/methods-bzip2.zip')
        assert ei.value.status == 500 and ei.value.kind == 'fetch'
        hub.fail = OSError('no route')
        with pytest.raises(ZipFetchError) as ei:
            hf_zip_list_files('o/r', 'a/methods-bzip2.zip')
        assert ei.value.status is None

    @pytest.mark.parametrize('error', ['status', 'name'])
    def test_what_the_hub_says_about_a_missing_repository_is_not_hidden(self, hub, error):
        class Missing(Exception):
            response = SimpleNamespace(status_code=404)

        class RepositoryNotFoundError(Exception):
            pass

        hub.fail = Missing('404') if error == 'status' else RepositoryNotFoundError('no such repository')
        with pytest.raises((Missing, RepositoryNotFoundError)):
            hf_zip_list_files('o/r', 'a/methods-bzip2.zip')

    def test_no_cache_reads_the_directory_every_time(self, hub):
        hf_zip_get_index('o/r', 'a/methods-bzip2.zip', no_cache=True)
        hf_zip_get_index('o/r', 'a/methods-bzip2.zip', no_cache=True)
        assert len(hub.fetches) == 2
        hf_zip_get_index('o/r', 'a/methods-bzip2.zip')
        hf_zip_get_index('o/r', 'a/methods-bzip2.zip')
        assert len(hub.fetches) == 3

    def test_a_limit_below_the_window_does_not_fetch_a_whole_window(self, hub, tmp_path):
        import zipfile
        path = str(tmp_path / 'big.zip')
        with zipfile.ZipFile(path, 'w', zipfile.ZIP_STORED) as zf:
            zf.writestr(zipfile.ZipInfo('big.bin', date_time=(2024, 1, 2, 3, 4, 6)), os.urandom(12 << 20))
        hub.files['a/big.zip'] = path
        hf_zip_get_index('o/r', 'a/big.zip')
        hub.fetches.clear()
        assert len(hf_zip_file_read('o/r', 'a/big.zip', 'big.bin', limit=1 << 20)) == 1 << 20
        assert sum(length for _, _, length, _ in hub.fetches) < 2 << 20  # not the 8 MiB window of a remote source
        hub.fetches.clear()
        assert len(hf_zip_file_read('o/r', 'a/big.zip', 'big.bin')) == 12 << 20
        assert max(length for _, _, length, _ in hub.fetches) == 8 << 20  # a whole read still uses whole windows

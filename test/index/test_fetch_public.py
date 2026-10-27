"""``hfutils.index`` functions that read an archive of a repository, against a public indexed tar (see ``public_tar``)."""
import hashlib
import io
import os

import pytest
from hbutils.testing import isolated_directory

from hfutils.index import hf_tar_list_files, hf_tar_file_exists, hf_tar_file_info, hf_tar_file_size, \
    hf_tar_file_download, hf_tar_file_write_bytes
from .public_tar import kwargs, index, members, REPO, ARCHIVE, IDX_REPO, EMPTY_MEMBER  # noqa: F401


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


@pytest.mark.unittest
class TestIndexFetchPublic:
    def test_list_files(self, index):
        files = hf_tar_list_files(**kwargs())
        assert len(files) == len(index['files']) == 6775
        assert sorted(files) == sorted(index['files'])  # the names as the archive has them, './' included

    def test_exists(self, members):
        assert hf_tar_file_exists(file_in_archive=members['small'], **kwargs())
        assert hf_tar_file_exists(file_in_archive=f'./{members["small"]}', **kwargs())
        assert hf_tar_file_exists(file_in_archive=members['empty'], **kwargs())
        assert not hf_tar_file_exists(file_in_archive=members['small'] + '.not-there', **kwargs())

    def test_info_and_size(self, members):
        for key in ('small', 'medium', 'empty'):
            name = members[key]
            want = next(i for n, i in members['info'].items() if n == name)
            assert hf_tar_file_info(file_in_archive=name, **kwargs()) == want
            assert hf_tar_file_info(file_in_archive=f'./{name}', **kwargs()) == want
            assert hf_tar_file_size(file_in_archive=name, **kwargs()) == want['size']
        with pytest.raises(FileNotFoundError):
            hf_tar_file_info(file_in_archive='not-there.jpg', **kwargs())
        with pytest.raises(FileNotFoundError):
            hf_tar_file_size(file_in_archive='not-there.jpg', **kwargs())

    @pytest.mark.parametrize('key', ['small', 'medium'])
    def test_download(self, members, key):
        name, want = members[key], members['info'][members[key]]
        with isolated_directory():
            hf_tar_file_download(file_in_archive=name, local_file='out.bin', **kwargs())
            with open('out.bin', 'rb') as f:
                data = f.read()
            assert len(data) == want['size'] and _sha256(data) == want['sha256']

    def test_download_into_a_new_directory_and_with_the_dot_prefix(self, members):
        name, want = members['small'], members['info'][members['small']]
        with isolated_directory():
            hf_tar_file_download(file_in_archive=f'./{name}', local_file='a/b/out.bin', **kwargs())
            with open('a/b/out.bin', 'rb') as f:
                assert _sha256(f.read()) == want['sha256']

    def test_download_is_skipped_when_the_file_is_already_right(self, members):
        name, want = members['small'], members['info'][members['small']]
        with isolated_directory():
            hf_tar_file_download(file_in_archive=name, local_file='out.bin', **kwargs())
            first = os.stat('out.bin').st_mtime_ns
            hf_tar_file_download(file_in_archive=name, local_file='out.bin', **kwargs())  # nothing is requested this time
            assert os.stat('out.bin').st_mtime_ns == first
            with open('out.bin', 'rb') as f:
                assert _sha256(f.read()) == want['sha256']

    def test_download_replaces_a_wrong_file(self, members):
        name, want = members['small'], members['info'][members['small']]
        with isolated_directory():
            with open('out.bin', 'wb') as f:
                f.write(b'something else' * 10)
            hf_tar_file_download(file_in_archive=name, local_file='out.bin', **kwargs())
            with open('out.bin', 'rb') as f:
                assert _sha256(f.read()) == want['sha256']

    def test_download_empty_member(self, members):
        with isolated_directory():
            hf_tar_file_download(file_in_archive=members['empty'], local_file='empty', **kwargs())
            assert os.path.getsize('empty') == 0

    def test_download_not_found(self):
        with isolated_directory(), pytest.raises(FileNotFoundError):
            hf_tar_file_download(file_in_archive='not-there.jpg', local_file='out.bin', **kwargs())

    @pytest.mark.parametrize('key', ['small', 'medium'])
    def test_write_bytes(self, members, key):
        name, want = members[key], members['info'][members[key]]
        with io.BytesIO() as bf:
            hf_tar_file_write_bytes(file_in_archive=name, bin_file=bf, **kwargs())
            assert len(bf.getvalue()) == want['size'] and _sha256(bf.getvalue()) == want['sha256']

    def test_write_bytes_appends_to_what_is_there(self, members):
        name, want = members['small'], members['info'][members['small']]
        with io.BytesIO() as bf:
            bf.write(b'append_prefix_')
            hf_tar_file_write_bytes(file_in_archive=name, bin_file=bf, **kwargs())
            assert bf.getvalue().startswith(b'append_prefix_')
            assert _sha256(bf.getvalue()[len(b'append_prefix_'):]) == want['sha256']

    def test_write_bytes_to_a_file(self, members):
        name, want = members['small'], members['info'][members['small']]
        with isolated_directory():
            with open('out.bin', 'wb') as bf:
                hf_tar_file_write_bytes(file_in_archive=name, bin_file=bf, **kwargs())
            with open('out.bin', 'rb') as f:
                assert _sha256(f.read()) == want['sha256']

    def test_write_bytes_empty_member(self, members):
        with io.BytesIO() as bf:
            bf.write(b'prefix')
            hf_tar_file_write_bytes(file_in_archive=members['empty'], bin_file=bf, **kwargs())
            assert bf.getvalue() == b'prefix'

    def test_write_bytes_not_found(self):
        with io.BytesIO() as bf, pytest.raises(FileNotFoundError):
            hf_tar_file_write_bytes(file_in_archive='not-there.jpg', bin_file=bf, **kwargs())

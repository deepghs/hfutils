import os
import pathlib

import pytest
from hbutils.testing import disable_output, isolated_directory
from huggingface_hub import hf_hub_url

from hfutils.archive import archive_unpack
from hfutils.operate import upload_directory_as_directory, upload_file_to_file, upload_directory_as_archive
from hfutils.utils import download_file
from test.testings import get_testfile


@pytest.fixture()
def hf_repo_with_files(hf_repo, hf_client):
    with disable_output():
        hf_client.upload_file(
            repo_id=hf_repo,
            repo_type='dataset',
            path_or_fileobj=get_testfile('raw', '1.txt'),
            path_in_repo='bullshit.txt'
        )
        hf_client.upload_file(
            repo_id=hf_repo,
            repo_type='dataset',
            path_or_fileobj=get_testfile('raw', '1.txt'),
            path_in_repo='README.md'
        )
    yield hf_repo


@pytest.mark.unittest
class TestOperateUpload:
    def test_upload_file_to_file(self, hf_repo, hf_fs):
        upload_file_to_file(
            get_testfile('raw.tar'),
            repo_id=hf_repo,
            file_in_repo='kkk/raw_remote.tar'
        )

        assert hf_fs.read_text(f'datasets/{hf_repo}/kkk/raw_remote.tar') == \
               pathlib.Path(get_testfile('raw.tar')).read_text()

    def test_upload_directory_as_archive(self, hf_repo, hf_fs, raw_dir, check_unpack_dir):
        upload_directory_as_archive(
            raw_dir,
            repo_id=hf_repo,
            archive_in_repo='tt/raw_remote.zip',
        )

        with isolated_directory():
            download_file(hf_hub_url(
                repo_id=hf_repo,
                repo_type='dataset',
                filename='tt/raw_remote.zip'
            ), 'raw_downloaded.zip')

            os.makedirs('dst', exist_ok=True)
            archive_unpack('raw_downloaded.zip', 'dst')
            check_unpack_dir('dst')

    def test_upload_directory_as_directory(self, hf_repo_with_files, hf_fs, raw_dir):
        upload_directory_as_directory(
            raw_dir,
            repo_id=hf_repo_with_files,
            path_in_repo='.',
        )

        assert hf_fs.read_text(f'datasets/{hf_repo_with_files}/1.txt').splitlines(keepends=False) == \
               pathlib.Path(get_testfile(raw_dir, '1.txt')).read_text().splitlines(keepends=False)
        assert hf_fs.read_text(f'datasets/{hf_repo_with_files}/README.md').splitlines(keepends=False) == \
               pathlib.Path(get_testfile(raw_dir, 'README.md')).read_text().splitlines(keepends=False)
        assert hf_fs.read_text(f'datasets/{hf_repo_with_files}/subdir/script.py').splitlines(keepends=False) == \
               pathlib.Path(get_testfile(raw_dir, 'subdir', 'script.py')).read_text().splitlines(keepends=False)
        assert hf_fs.exists(f'datasets/{hf_repo_with_files}/.gitattributes')
        assert hf_fs.exists(f'datasets/{hf_repo_with_files}/bullshit.txt')

    def test_upload_directory_as_directory_clear(self, hf_repo_with_files, hf_fs, raw_dir):
        upload_directory_as_directory(
            raw_dir,
            repo_id=hf_repo_with_files,
            path_in_repo='.',
            clear=True,
        )

        assert hf_fs.read_text(f'datasets/{hf_repo_with_files}/1.txt').splitlines(keepends=False) == \
               pathlib.Path(get_testfile(raw_dir, '1.txt')).read_text().splitlines(keepends=False)
        assert hf_fs.read_text(f'datasets/{hf_repo_with_files}/README.md').splitlines(keepends=False) == \
               pathlib.Path(get_testfile(raw_dir, 'README.md')).read_text().splitlines(keepends=False)
        assert hf_fs.read_text(f'datasets/{hf_repo_with_files}/subdir/script.py').splitlines(keepends=False) == \
               pathlib.Path(get_testfile(raw_dir, 'subdir', 'script.py')).read_text().splitlines(keepends=False)
        assert hf_fs.exists(f'datasets/{hf_repo_with_files}/.gitattributes')
        assert not hf_fs.exists(f'datasets/{hf_repo_with_files}/bullshit.txt')

    def test_upload_directory_as_directory_in_subdir(self, hf_repo_with_files, hf_fs, raw_dir):
        upload_directory_as_directory(
            raw_dir,
            repo_id=hf_repo_with_files,
            path_in_repo='ttt',
        )

        assert hf_fs.read_text(f'datasets/{hf_repo_with_files}/ttt/1.txt').splitlines(keepends=False) == \
               pathlib.Path(get_testfile(raw_dir, '1.txt')).read_text().splitlines(keepends=False)
        assert hf_fs.read_text(f'datasets/{hf_repo_with_files}/ttt/README.md').splitlines(keepends=False) == \
               pathlib.Path(get_testfile(raw_dir, 'README.md')).read_text().splitlines(keepends=False)
        assert hf_fs.read_text(f'datasets/{hf_repo_with_files}/ttt/subdir/script.py').splitlines(keepends=False) == \
               pathlib.Path(get_testfile(raw_dir, 'subdir', 'script.py')).read_text().splitlines(keepends=False)

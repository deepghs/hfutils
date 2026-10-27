"""``download_archive_as_directory`` against a public repository: ``deepghs/test_nested_dataset`` holds small tar archives."""
import os
import tarfile

import pytest
from hbutils.testing import isolated_directory
from huggingface_hub import hf_hub_download

from hfutils.operate import download_archive_as_directory
from test.testings import dir_compare

REPO = 'deepghs/test_nested_dataset'
ARCHIVE = 'images/20240810/20240810025642281532_4c13dc63689d93e25a5de44bc9add04ea7d56162__narugo.tar'


def extracted_by_tarfile(directory):
    """The expected content, from a source that is not hfutils: the archive downloaded as it is, opened by ``tarfile``."""
    path = hf_hub_download(repo_id=REPO, repo_type='dataset', filename=ARCHIVE)
    os.makedirs(directory, exist_ok=True)
    with tarfile.open(path) as tf:
        names = tf.getnames()
        tf.extractall(directory)
    return names


@pytest.mark.unittest
class TestOperateDownloadPublic:
    def test_download_archive_as_directory(self):
        with isolated_directory():
            names = extracted_by_tarfile('expected')
            assert len([n for n in names if n not in ('.', '')]) > 0

            download_archive_as_directory('download_dir', repo_id=REPO, file_in_repo=ARCHIVE)
            dir_compare('expected', 'download_dir')

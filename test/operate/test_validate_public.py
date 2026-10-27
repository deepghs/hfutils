"""``is_local_file_ready`` against a public repository: ``deepghs/public_unittest_repo`` has LFS files and text files."""
import pytest
from huggingface_hub import hf_hub_download
from huggingface_hub.utils import EntryNotFoundError

from hfutils.operate import is_local_file_ready

REPO = 'deepghs/public_unittest_repo'


def _download(filename):
    return hf_hub_download(repo_id=REPO, repo_type='dataset', filename=filename)


def _ready(file_in_repo, local_file):
    return is_local_file_ready(repo_id=REPO, repo_type='dataset', file_in_repo=file_in_repo, local_file=local_file)


@pytest.mark.unittest
class TestOperateValidatePublic:
    def test_lfs_files_are_compared_by_sha256(self):
        animes, episodes = _download('animes.parquet'), _download('episodes.parquet')
        assert _ready('animes.parquet', animes)
        assert _ready('episodes.parquet', episodes)
        assert not _ready('animes.parquet', episodes)  # same kind of file, other bytes
        assert not _ready('episodes.parquet', animes)

    def test_text_files_are_compared_by_git_blob_hash(self):
        readme, attributes = _download('README.md'), _download('.gitattributes')
        assert _ready('README.md', readme)
        assert _ready('.gitattributes', attributes)
        assert not _ready('README.md', attributes)
        assert not _ready('.gitattributes', readme)

    def test_a_text_file_is_never_an_lfs_one(self):
        animes, readme = _download('animes.parquet'), _download('README.md')
        assert not _ready('animes.parquet', readme)
        assert not _ready('README.md', animes)

    def test_file_not_found(self):
        with pytest.raises(EntryNotFoundError):
            _ready('this_file_does_not_exist.txt', _download('README.md'))

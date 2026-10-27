"""``hf_tar_validate`` against a public indexed tar (see ``public_tar``)."""
import pytest
from huggingface_hub.utils import EntryNotFoundError

from hfutils.index import hf_tar_validate
from .public_tar import kwargs, OTHER_IDX_FILE, REPO, ARCHIVE, IDX_REPO


@pytest.mark.unittest
class TestIndexValidatePublic:
    def test_up_to_date(self):
        assert hf_tar_validate(**kwargs())

    def test_the_index_of_another_archive_is_outdated(self):
        # a different archive has a different size and hash: the index no longer describes this one
        assert not hf_tar_validate(idx_file_in_repo=OTHER_IDX_FILE, **kwargs())

    def test_archive_not_found(self):
        with pytest.raises(EntryNotFoundError):
            hf_tar_validate(repo_id=REPO, archive_in_repo='original/not-there.tar', idx_repo_id=IDX_REPO)

    def test_index_repository_not_found(self):
        assert not hf_tar_validate(repo_id=REPO, archive_in_repo=ARCHIVE, idx_repo_id='deepghs/a_repo_that_does_not_exist')

    def test_index_file_not_found(self):
        assert not hf_tar_validate(idx_file_in_repo='original/not-there.json', **kwargs())

    def test_archive_is_a_directory(self):
        with pytest.raises(IsADirectoryError):
            hf_tar_validate(repo_id=REPO, archive_in_repo='original', idx_repo_id=IDX_REPO)

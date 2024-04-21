import pytest
from huggingface_hub.utils import EntryNotFoundError

from hfutils.index import hf_tar_validate


@pytest.mark.unittest
class TestIndexValidate:
    def test_hf_tar_file_download_lfs(self):
        assert hf_tar_validate(
            repo_id='narugo/test_cos5t_tars',
            archive_in_repo='mashu_skins.tar',
        )

    def test_hf_tar_file_download_lfs_extra(self):
        assert not hf_tar_validate(
            repo_id='narugo/test_cos5t_tars',
            archive_in_repo='mashu_skins.tar',
            idx_file_in_repo='ex3.json'
        )

    def test_hf_tar_file_download_lfs_not_found(self):
        with pytest.raises(EntryNotFoundError):
            hf_tar_validate(
                repo_id='narugo/test_cos5t_tars',
                archive_in_repo='mashu_skins_not_found.tar',
            )

    def test_hf_tar_file_download_lfs_is_directory(self):
        with pytest.raises(IsADirectoryError):
            hf_tar_validate(
                repo_id='narugo/test_cos5t_tars',
                archive_in_repo='1001-1500',
            )

import pytest
from huggingface_hub import hf_hub_download
from huggingface_hub.utils import EntryNotFoundError

from hfutils.operate import is_local_file_ready


@pytest.fixture(scope='session')
def surtr_dataset_zip():
    return hf_hub_download(
        repo_id='narugo/test_ds_repo',
        repo_type='dataset',
        filename='surtr_dataset.zip'
    )


@pytest.fixture(scope='session')
def surtr_dataset_zip_x():
    return hf_hub_download(
        repo_id='narugo/test_ds_repo',
        repo_type='dataset',
        filename='surtr_dataset.zip_x'
    )


@pytest.fixture(scope='session')
def git_attr():
    return hf_hub_download(
        repo_id='narugo/test_ds_repo',
        repo_type='dataset',
        filename='.gitattributes',
    )


@pytest.fixture(scope='session')
def raw_text():
    return hf_hub_download(
        repo_id='narugo/test_ds_repo',
        repo_type='dataset',
        filename='raw_text',
    )


@pytest.mark.unittest
class TestOperateValidate:
    def test_is_local_file_ready_lfs(self, surtr_dataset_zip, surtr_dataset_zip_x, git_attr):
        assert is_local_file_ready(
            repo_id='narugo/test_ds_repo',
            repo_type='dataset',
            file_in_repo='surtr_dataset.zip',
            local_file=surtr_dataset_zip,
        )
        assert not is_local_file_ready(
            repo_id='narugo/test_ds_repo',
            repo_type='dataset',
            file_in_repo='surtr_dataset.zip',
            local_file=surtr_dataset_zip_x,
        )
        assert not is_local_file_ready(
            repo_id='narugo/test_ds_repo',
            repo_type='dataset',
            file_in_repo='surtr_dataset.zip_x',
            local_file=surtr_dataset_zip,
        )
        assert is_local_file_ready(
            repo_id='narugo/test_ds_repo',
            repo_type='dataset',
            file_in_repo='surtr_dataset.zip_x',
            local_file=surtr_dataset_zip_x,
        )

    def test_is_local_file_ready_text(self, surtr_dataset_zip, surtr_dataset_zip_x, git_attr, raw_text):
        assert not is_local_file_ready(
            repo_id='narugo/test_ds_repo',
            repo_type='dataset',
            file_in_repo='surtr_dataset.zip',
            local_file=git_attr,
        )
        assert not is_local_file_ready(
            repo_id='narugo/test_ds_repo',
            repo_type='dataset',
            file_in_repo='surtr_dataset.zip_x',
            local_file=git_attr,
        )

        assert is_local_file_ready(
            repo_id='narugo/test_ds_repo',
            repo_type='dataset',
            file_in_repo='.gitattributes',
            local_file=git_attr,
        )
        assert not is_local_file_ready(
            repo_id='narugo/test_ds_repo',
            repo_type='dataset',
            file_in_repo='raw_text',
            local_file=git_attr,
        )
        assert not is_local_file_ready(
            repo_id='narugo/test_ds_repo',
            repo_type='dataset',
            file_in_repo='.gitattributes',
            local_file=raw_text,
        )
        assert is_local_file_ready(
            repo_id='narugo/test_ds_repo',
            repo_type='dataset',
            file_in_repo='raw_text',
            local_file=raw_text,
        )

    def test_file_not_found(self, raw_text):
        with pytest.raises(EntryNotFoundError):
            is_local_file_ready(
                repo_id='narugo/test_ds_repo',
                repo_type='dataset',
                file_in_repo='raw_text_not_exist',
                local_file=raw_text,
            )

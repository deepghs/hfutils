import pytest

from hfutils.repository import hf_hub_repo_url


@pytest.mark.unittest
class TestRepositoryBase:
    def test_hf_hub_repo_url(self):
        assert hf_hub_repo_url(repo_id='deepghs/mydataset') == 'https://huggingface.co/datasets/deepghs/mydataset'
        assert hf_hub_repo_url(repo_id='deepghs/model', repo_type='model') == 'https://huggingface.co/deepghs/model'
        assert hf_hub_repo_url(repo_id='deepghs/mydataset', repo_type='dataset') == \
               'https://huggingface.co/datasets/deepghs/mydataset'
        assert hf_hub_repo_url(repo_id='deepghs/space', repo_type='space') == \
               'https://huggingface.co/spaces/deepghs/space'

    def test_hf_hub_repo_url_invalid_type(self):
        with pytest.raises(ValueError):
            hf_hub_repo_url(repo_id='deepghs/model', repo_type='???')

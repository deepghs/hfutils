import os
import shutil
from unittest.mock import patch

import pytest
from hbutils.testing import isolated_directory
from huggingface_hub import HfApi

from hfutils.repository import hf_hub_clone
from ..testings import get_testfile, dir_compare


@pytest.fixture()
def no_hf_token():
    def _get_hf_client():
        return HfApi(token='')

    with patch('hfutils.entry.whoami.get_hf_client', _get_hf_client), \
            patch.dict(os.environ, {'HF_TOKEN': ''}):
        yield


@pytest.mark.unittest
class TestRepositoryClone:
    def test_hf_hub_clone(self):
        with isolated_directory():
            hf_hub_clone(
                repo_id='deepghs/private_unittest_repo',
                dst_dir='repo',
            )

            os.remove(os.path.join('repo', '.gitattributes'))
            shutil.rmtree(os.path.join('repo', '.git'))

            dir_compare(get_testfile('clone'), 'repo')

    def test_hf_hub_clone_no_token(self, no_hf_token):
        with isolated_directory():
            hf_hub_clone(
                repo_id='deepghs/public_unittest_repo',
                dst_dir='repo',
            )

            os.remove(os.path.join('repo', '.gitattributes'))
            shutil.rmtree(os.path.join('repo', '.git'))

            dir_compare(get_testfile('clone'), 'repo')

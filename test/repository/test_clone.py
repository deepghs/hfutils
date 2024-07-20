import os
import shutil
from unittest.mock import patch

import pytest
from hbutils.testing import isolated_directory
from huggingface_hub import HfApi

from hfutils.repository import hf_hub_clone
from hfutils.utils import TemporaryDirectory
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
        with isolated_directory(), TemporaryDirectory() as td:
            hf_hub_clone(
                repo_id='deepghs/private_unittest_repo',
                dst_dir='repo',
            )

            # dont delete .git/.gitattributes here
            # on windows, this will cause permission error
            for f in os.listdir('repo'):
                if not f.startswith('.git'):
                    file = os.path.join('repo', f)
                    if os.path.isfile(file):
                        shutil.copyfile(file, os.path.join(td, f))
                    elif os.path.isdir(file):
                        shutil.copytree(file, os.path.join(td, f))
            dir_compare(get_testfile('clone'), td)

    def test_hf_hub_clone_no_token(self, no_hf_token):
        with isolated_directory(), TemporaryDirectory() as td:
            hf_hub_clone(
                repo_id='deepghs/public_unittest_repo',
                dst_dir='repo',
            )

            # dont delete .git/.gitattributes here
            # on windows, this will cause permission error
            for f in os.listdir('repo'):
                if not f.startswith('.git'):
                    file = os.path.join('repo', f)
                    if os.path.isfile(file):
                        shutil.copyfile(file, os.path.join(td, f))
                    elif os.path.isdir(file):
                        shutil.copytree(file, os.path.join(td, f))
            dir_compare(get_testfile('clone'), td)

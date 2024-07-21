import os
import shutil
from unittest.mock import patch

import pytest
from hbutils.testing import simulate_entry, isolated_directory
from huggingface_hub import HfApi

from hfutils.entry import hfutilscli
from hfutils.utils import TemporaryDirectory
from test.testings import get_testfile, dir_compare


@pytest.fixture()
def no_hf_token():
    def _get_hf_client(*args, **kwargs):
        _ = args, kwargs
        return HfApi(token='')

    with patch('hfutils.repository.clone.get_hf_client', _get_hf_client), \
            patch.dict(os.environ, {'HF_TOKEN': ''}):
        yield


@pytest.mark.unittest
class TestEntryClone:
    def test_clone_private(self):
        with isolated_directory(), TemporaryDirectory() as td:
            result = simulate_entry(hfutilscli, [
                'hfutils', 'clone', '-r', 'deepghs/private_unittest_repo', '-o', 'repo'
            ])
            assert result.exitcode == 0

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

    def test_clone_public(self, no_hf_token):
        with isolated_directory(), TemporaryDirectory() as td:
            result = simulate_entry(hfutilscli, [
                'hfutils', 'clone', '-r', 'deepghs/public_unittest_repo',
            ])
            assert result.exitcode == 0

            # dont delete .git/.gitattributes here
            # on windows, this will cause permission error
            for f in os.listdir('public_unittest_repo'):
                if not f.startswith('.git'):
                    file = os.path.join('public_unittest_repo', f)
                    if os.path.isfile(file):
                        shutil.copyfile(file, os.path.join(td, f))
                    elif os.path.isdir(file):
                        shutil.copytree(file, os.path.join(td, f))
            dir_compare(get_testfile('clone'), td)

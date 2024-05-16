import os
from unittest.mock import patch

import click
import pytest
from hbutils.testing import simulate_entry
from huggingface_hub import HfApi

from hfutils.entry import hfutilscli


@pytest.fixture()
def no_hf_token():
    def _get_hf_client():
        return HfApi(token='')

    with patch('hfutils.entry.ls_repo.get_hf_client', _get_hf_client), \
            patch.dict(os.environ, {'HF_TOKEN': ''}):
        yield


@pytest.mark.unittest
class TestEntryLsRepo:
    def test_ls_repo(self):
        result = simulate_entry(hfutilscli, [
            'hfutils', 'ls_repo',
        ])
        assert result.exitcode == 0
        repos = click.unstyle(result.stdout).splitlines(keepends=False)
        assert 'narugo/manual_packs' in repos
        assert 'narugo/csip_v1_info' in repos

    def test_ls_repo_space(self):
        result = simulate_entry(hfutilscli, [
            'hfutils', 'ls_repo', '-t', 'space',
        ])
        assert result.exitcode == 0
        repos = click.unstyle(result.stdout).splitlines(keepends=False)
        assert 'narugo/jupyterlab' in repos
        assert 'narugo/CDC_anime_demo' in repos

    def test_ls_repo_model(self):
        result = simulate_entry(hfutilscli, [
            'hfutils', 'ls_repo', '-t', 'model',
        ])
        assert result.exitcode == 0
        repos = click.unstyle(result.stdout).splitlines(keepends=False)
        assert 'narugo/gchar_models' in repos
        assert 'narugo/test_v1.5_kristen' in repos
        assert 'narugo/test_v1.5_nian' in repos

    def test_ls_repo_anonymous(self, no_hf_token):
        result = simulate_entry(hfutilscli, [
            'hfutils', 'ls_repo',
        ])
        assert result.exitcode == 0x31
        stdout_lines = click.unstyle(result.stdout).splitlines(keepends=False)
        assert len(stdout_lines) == 0
        stderr_lines = click.unstyle(result.stderr).splitlines(keepends=False)
        assert 'Authentication failed.' in stderr_lines

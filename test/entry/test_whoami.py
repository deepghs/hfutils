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

    with patch('hfutils.entry.whoami.get_hf_client', _get_hf_client), \
            patch.dict(os.environ, {'HF_TOKEN': ''}):
        yield


@pytest.mark.unittest
class TestEntryWhoami:
    def test_simple_whoami(self):
        result = simulate_entry(hfutilscli, [
            'hfutils', 'whoami',
        ])
        assert result.exitcode == 0
        text = click.unstyle(result.stdout)
        lines = text.splitlines(keepends=False)
        assert 'Hi, @narugo (full name: narugo1992).' in lines
        assert 'You can access all resources with this identification.' in lines
        for org_info in [
            '@waifu-research-department (full name: The Waifu Research Department)',
            '@deepghs (full name: DeepGHS)',
            '@CyberHarem (full name: DeepGHS CyberHarem)',
            '@BangumiBase (full name: DeepGHS BangumiBase)',
            '@DeepBase (full name: DeepBase)',
            '@CyberHaremXL (full name: DeepGHS CyberHarem for SDXL)',
            '@AppleHarem (full name: LittleApple AppleHarem)',
        ]:
            assert org_info in text, f'Organization {org_info!r} not found.'

    def test_whoami_guest(self, no_hf_token):
        result = simulate_entry(hfutilscli, [
            'hfutils', 'whoami',
        ])
        assert result.exitcode == 0
        text = click.unstyle(result.stdout)
        lines = text.splitlines(keepends=False)
        assert 'Hi, Guest (not authenticated).' in lines
        assert 'No token for huggingface authentication found.' in lines
        assert 'If you need to access more, just set `HF_TOKEN` environment variable, or use `huggingface-cli login`.' in lines

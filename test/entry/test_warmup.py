import os

import pytest
from hbutils.testing import simulate_entry, isolated_directory
from huggingface_hub import hf_hub_download

from hfutils.cache import delete_cache
from hfutils.entry import hfutilscli
from ..testings import get_testfile, file_compare, dir_compare


@pytest.fixture()
def clean_cache():
    delete_cache(repo_id='deepghs/game_character_skins', repo_type='dataset')
    try:
        yield
    finally:
        delete_cache(repo_id='deepghs/game_character_skins', repo_type='dataset')


@pytest.mark.unittest
class TestEntryWarmup:
    def test_warmup_file(self, clean_cache):
        target_file = get_testfile('mashu.png')
        with isolated_directory():
            result = simulate_entry(hfutilscli, [
                'hfutils', 'warmup',
                '-r', 'deepghs/game_character_skins',
                '-f', 'fgo/1/常夏的泳装Ver_02.png',
            ])
            assert result.exitcode == 0

            dst_file = os.path.normpath(os.path.join(hf_hub_download(
                repo_id='deepghs/game_character_skins',
                repo_type='dataset',
                filename='fgo/1/第1阶段.png',
            ), '..', '常夏的泳装Ver_02.png'))
            file_compare(target_file, dst_file)

    def test_warmup_directory(self, clean_cache):
        target_dir = get_testfile('skin_mashu')
        with isolated_directory():
            result = simulate_entry(hfutilscli, [
                'hfutils', 'warmup',
                '-r', 'deepghs/game_character_skins',
                '-d', 'fgo/1',
            ])
            assert result.exitcode == 0

            dst_dir = os.path.normpath(os.path.join(hf_hub_download(
                repo_id='deepghs/game_character_skins',
                repo_type='dataset',
                filename='fgo/1/常夏的泳装Ver_02.png',
            ), '..'))
            dir_compare(target_dir, dst_dir)

    def test_no_assign(self, clean_cache):
        result = simulate_entry(hfutilscli, [
            'hfutils', 'warmup',
            '-r', 'deepghs/game_character_skins',
        ])
        assert result.exitcode == 0x41

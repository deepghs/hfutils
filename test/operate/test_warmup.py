import os.path

import pytest
from huggingface_hub import hf_hub_download

from hfutils.cache import delete_cache
from hfutils.operate import hf_warmup_file, hf_warmup_directory
from ..testings import get_testfile, file_compare, dir_compare


@pytest.fixture()
def clean_cache():
    delete_cache(repo_id='deepghs/game_character_skins', repo_type='dataset')
    try:
        yield
    finally:
        delete_cache(repo_id='deepghs/game_character_skins', repo_type='dataset')


@pytest.mark.unittest
class TestOperateWarmup:
    def test_hf_warmup_file(self, clean_cache):
        target_file = get_testfile('mashu.png')
        dst_file = hf_warmup_file(
            repo_id='deepghs/game_character_skins',
            filename='fgo/1/常夏的泳装Ver_02.png',
        )
        file_compare(target_file, dst_file)

    def test_hf_warmup_directory(self, clean_cache):
        target_dir = get_testfile('skin_mashu')
        hf_warmup_directory(
            repo_id='deepghs/game_character_skins',
            dir_in_repo='fgo/1',
        )
        dst_dir = os.path.normpath(os.path.join(hf_hub_download(
            repo_id='deepghs/game_character_skins',
            repo_type='dataset',
            filename='fgo/1/常夏的泳装Ver_02.png',
        ), '..'))
        dir_compare(target_dir, dst_dir)

    def test_hf_warmup_directory_with_pattern(self, clean_cache):
        target_dir = get_testfile('skin_mashu_pattern')
        hf_warmup_directory(
            repo_id='deepghs/game_character_skins',
            dir_in_repo='fgo/1',
            pattern='第*.png',
        )
        dst_dir = os.path.normpath(os.path.join(hf_hub_download(
            repo_id='deepghs/game_character_skins',
            repo_type='dataset',
            filename='fgo/1/第1阶段.png',
        ), '..'))
        dir_compare(target_dir, dst_dir)

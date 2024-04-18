from unittest.mock import patch

import pytest
from hbutils.testing import isolated_directory

from hfutils.operate import download_file_to_file, download_archive_as_directory, download_directory_as_directory
from test.testings import get_testfile, file_compare, dir_compare


@pytest.mark.unittest
class TestOperateDownload:
    def test_download_file_to_file(self):
        target_file = get_testfile('mashu.png')
        with isolated_directory():
            download_file_to_file(
                'mashu_download.png',
                repo_id='deepghs/game_character_skins',
                file_in_repo='fgo/1/常夏的泳装Ver_02.png',
            )
            file_compare(target_file, 'mashu_download.png')

    def test_download_archive_as_directory(self):
        target_dir = get_testfile('surtr_ds')
        with isolated_directory():
            download_archive_as_directory(
                'download_dir',
                repo_id='narugo/test_ds_repo',
                file_in_repo='surtr_dataset.zip',
            )
            dir_compare(target_dir, 'download_dir')

    def test_download_directory_as_directory(self):
        target_dir = get_testfile('skin_mashu')

        call_times = 0

        def _my_download(*args, **kwargs):
            nonlocal call_times
            call_times += 1
            return download_file_to_file(*args, **kwargs)

        with patch('hfutils.operate.download.download_file_to_file', _my_download), \
                isolated_directory():
            download_directory_as_directory(
                'download_dir',
                repo_id='deepghs/game_character_skins',
                dir_in_repo='fgo/1',
            )
            dir_compare(target_dir, 'download_dir')

        assert call_times == 17

    def test_download_directory_as_directory_partial(self):
        target_dir = get_testfile('skin_mashu')
        src_dir = get_testfile('skin_mashu_p')

        call_times = 0

        def _my_download(*args, **kwargs):
            nonlocal call_times
            call_times += 1
            return download_file_to_file(*args, **kwargs)

        with patch('hfutils.operate.download.download_file_to_file', _my_download), \
                isolated_directory({'download_dir': src_dir}):
            download_directory_as_directory(
                'download_dir',
                repo_id='deepghs/game_character_skins',
                dir_in_repo='fgo/1',
            )
            dir_compare(target_dir, 'download_dir')

        assert call_times == 6

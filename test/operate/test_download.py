from unittest.mock import patch

import pytest
from hbutils.testing import isolated_directory

from hfutils.operate import download_file_to_file, download_archive_as_directory, download_directory_as_directory
from hfutils.operate.download import _raw_download_file
from test.testings import get_testfile, file_compare, dir_compare


@pytest.mark.unittest
class TestOperateDownload:
    def test_download_file_to_file(self):
        target_file = get_testfile('mashu.png')

        call_times = 0

        def _my_download(*args, **kwargs):
            nonlocal call_times
            call_times += 1
            return _raw_download_file(*args, **kwargs)

        with patch('hfutils.operate.download._raw_download_file', _my_download), \
                isolated_directory():
            download_file_to_file(
                'mashu_download.png',
                repo_id='deepghs/game_character_skins',
                file_in_repo='fgo/1/常夏的泳装Ver_02.png',
            )
            file_compare(target_file, 'mashu_download.png')

        assert call_times == 1

    def test_download_file_to_file_skip(self):
        target_file = get_testfile('mashu.png')

        call_times = 0

        def _my_download(*args, **kwargs):
            nonlocal call_times
            call_times += 1
            return _raw_download_file(*args, **kwargs)

        with patch('hfutils.operate.download._raw_download_file', _my_download), \
                isolated_directory({'mashu_download.png': target_file}):
            download_file_to_file(
                'mashu_download.png',
                repo_id='deepghs/game_character_skins',
                file_in_repo='fgo/1/常夏的泳装Ver_02.png',
            )
            file_compare(target_file, 'mashu_download.png')

        assert call_times == 0

    def test_download_archive_as_directory(self):
        target_dir = get_testfile('surtr_ds')
        with isolated_directory():
            download_archive_as_directory(
                'download_dir',
                repo_id='narugo1992/test_ds_repo',
                file_in_repo='surtr_dataset.zip',
            )
            dir_compare(target_dir, 'download_dir')

    def test_download_directory_as_directory(self):
        target_dir = get_testfile('skin_mashu')

        call_times = 0

        def _my_download(*args, **kwargs):
            nonlocal call_times
            call_times += 1
            return _raw_download_file(*args, **kwargs)

        with patch('hfutils.operate.download._raw_download_file', _my_download), \
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
            return _raw_download_file(*args, **kwargs)

        with patch('hfutils.operate.download._raw_download_file', _my_download), \
                isolated_directory({'download_dir': src_dir}):
            download_directory_as_directory(
                'download_dir',
                repo_id='deepghs/game_character_skins',
                dir_in_repo='fgo/1',
            )
            dir_compare(target_dir, 'download_dir')

        assert call_times == 6

    def test_download_directory_as_directory_with_pattern(self):
        target_dir = get_testfile('skin_mashu_pattern')

        call_times = 0

        def _my_download(*args, **kwargs):
            nonlocal call_times
            call_times += 1
            return _raw_download_file(*args, **kwargs)

        with patch('hfutils.operate.download._raw_download_file', _my_download), \
                isolated_directory():
            download_directory_as_directory(
                'download_dir',
                repo_id='deepghs/game_character_skins',
                dir_in_repo='fgo/1',
                pattern='第*.png',
            )
            dir_compare(target_dir, 'download_dir')

        assert call_times == 4

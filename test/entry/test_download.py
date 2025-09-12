import pytest
from hbutils.testing import simulate_entry, isolated_directory

from hfutils.entry import hfutilscli
from test.testings import get_testfile, file_compare, dir_compare


@pytest.mark.unittest
class TestEntryDownload:
    def test_download_file_to_file(self):
        target_file = get_testfile('mashu.png')
        with isolated_directory():
            result = simulate_entry(hfutilscli, [
                'hfutils', 'download',
                '-r', 'deepghs/game_character_skins',
                '-f', 'fgo/1/常夏的泳装Ver_02.png',
                '-o', 'mashu_download.png'
            ])
            assert result.exitcode == 0
            file_compare(target_file, 'mashu_download.png')

    def test_download_archive_as_directory(self):
        target_dir = get_testfile('surtr_ds')
        with isolated_directory():
            result = simulate_entry(hfutilscli, [
                'hfutils', 'download',
                '-r', 'narugo1992/test_ds_repo',
                '-a', 'surtr_dataset.zip',
                '-o', 'download_dir'
            ])
            assert result.exitcode == 0
            dir_compare(target_dir, 'download_dir')

    def test_download_directory_as_directory(self):
        target_dir = get_testfile('skin_mashu')
        with isolated_directory():
            result = simulate_entry(hfutilscli, [
                'hfutils', 'download',
                '-r', 'deepghs/game_character_skins',
                '-d', 'fgo/1',
                '-o', 'download_dir'
            ])
            assert result.exitcode == 0
            dir_compare(target_dir, 'download_dir')

    def test_no_assign(self):
        result = simulate_entry(hfutilscli, [
            'hfutils', 'download',
            '-r', 'deepghs/game_character_skins',
            '-o', 'download_dir'
        ])
        assert result.exitcode == 0x11

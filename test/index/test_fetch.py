import pytest
from hbutils.testing import isolated_directory
from natsort import natsorted

from hfutils.index import hf_tar_list_files, hf_tar_file_exists, hf_tar_file_download
from test.testings import get_testfile, file_compare


@pytest.mark.unittest
class TestIndexFetch:
    def test_hf_tar_list_files(self):
        files = hf_tar_list_files(
            repo_id='narugo/test_cos5t_tars',
            archive_in_repo='mashu_skins.tar',
        )
        assert len(files) == 17
        assert natsorted(files) == [
            '.meta.json', 'Bright_Voyager.png', 'Grail_League_1星.png', 'Grail_League_2星.png', 'Grail_League_3星.png',
            'Grail_League_4星.png', 'Grail_League_5星.png', '奥特瑙斯.png', '奥特瑙斯_改建型.png', '常夏的泳装.png',
            '常夏的泳装Ver_02.png', '愚人节.png', '愚人节_奥特瑙斯.png', '第1阶段.png', '第2阶段.png', '第3阶段.png',
            '第4阶段.png'
        ]

    def test_hf_tar_file_exists(self):
        assert hf_tar_file_exists(
            repo_id='narugo/test_cos5t_tars',
            archive_in_repo='mashu_skins.tar',
            file_in_archive='.meta.json'
        )
        assert hf_tar_file_exists(
            repo_id='narugo/test_cos5t_tars',
            archive_in_repo='mashu_skins.tar',
            file_in_archive='愚人节_奥特瑙斯.png'
        )
        assert hf_tar_file_exists(
            repo_id='narugo/test_cos5t_tars',
            archive_in_repo='mashu_skins.tar',
            file_in_archive='./愚人节_奥特瑙斯.png'
        )
        assert not hf_tar_file_exists(
            repo_id='narugo/test_cos5t_tars',
            archive_in_repo='mashu_skins.tar',
            file_in_archive='愚人节奥特瑙斯.png'
        )

    def test_hf_tar_file_download_small(self):
        with isolated_directory():
            hf_tar_file_download(
                repo_id='narugo/test_cos5t_tars',
                archive_in_repo='mashu_skins.tar',
                file_in_archive='.meta.json',
                local_file='.meta.json'
            )
            file_compare(get_testfile('skin_mashu', '.meta.json'), '.meta.json')

    def test_hf_tar_file_download_lfs(self):
        with isolated_directory():
            hf_tar_file_download(
                repo_id='narugo/test_cos5t_tars',
                archive_in_repo='mashu_skins.tar',
                file_in_archive='./愚人节_奥特瑙斯.png',
                local_file='愚人节_奥特瑙斯.png'
            )
            file_compare(get_testfile('skin_mashu', '愚人节_奥特瑙斯.png'), '愚人节_奥特瑙斯.png')

    def test_hf_tar_file_download_not_found(self):
        with isolated_directory(), pytest.raises(FileNotFoundError):
            hf_tar_file_download(
                repo_id='narugo/test_cos5t_tars',
                archive_in_repo='mashu_skins.tar',
                file_in_archive='./愚人节奥特瑙斯.png',
                local_file='愚人节_奥特瑙斯.png'
            )

    def test_hf_tar_file_download_subdir(self):
        with isolated_directory():
            hf_tar_file_download(
                repo_id='narugo/test_cos5t_tars',
                archive_in_repo='ex3.tar',
                file_in_archive='artoria_caster_third_ascension_fate/sankaku_21305298.jpg',
                local_file='f/ac.jpg'
            )
            file_compare(get_testfile('sankaku_21305298.jpg'), 'f/ac.jpg')

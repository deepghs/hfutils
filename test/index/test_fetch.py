import io
import os.path
import pathlib
from unittest.mock import patch, MagicMock

import pytest
from hbutils.testing import isolated_directory
from natsort import natsorted

from hfutils.index import hf_tar_list_files, hf_tar_file_exists, hf_tar_file_download, hf_tar_file_info, \
    hf_tar_file_size, hf_tar_cache_reset, hf_tar_file_write_bytes
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

    def test_hf_tar_file_info(self):
        assert hf_tar_file_info(
            repo_id='narugo/test_cos5t_tars',
            archive_in_repo='mashu_skins.tar',
            file_in_archive='.meta.json'
        ) == {
                   'offset': 2725376,
                   'sha256': '4585b01c251a496b73cb231d29fc711cfb1d682a84334d95f6f5b6c1cc5b5222',
                   'size': 8968
               }
        assert hf_tar_file_info(
            repo_id='narugo/test_cos5t_tars',
            archive_in_repo='mashu_skins.tar',
            file_in_archive='愚人节_奥特瑙斯.png'
        ) == {
                   'offset': 3954176,
                   'sha256': '991497fa586f6f4529827e0f8f1f228c20ec9fb507c314ee9d20d47c46f26e89',
                   'size': 255276
               }
        assert hf_tar_file_info(
            repo_id='narugo/test_cos5t_tars',
            archive_in_repo='mashu_skins.tar',
            file_in_archive='./愚人节_奥特瑙斯.png'
        ) == {
                   'offset': 3954176,
                   'sha256': '991497fa586f6f4529827e0f8f1f228c20ec9fb507c314ee9d20d47c46f26e89',
                   'size': 255276
               }
        with pytest.raises(FileNotFoundError):
            _ = hf_tar_file_info(
                repo_id='narugo/test_cos5t_tars',
                archive_in_repo='mashu_skins.tar',
                file_in_archive='愚人节奥特瑙斯.png'
            )

    def test_hf_tar_file_size(self):
        assert hf_tar_file_size(
            repo_id='narugo/test_cos5t_tars',
            archive_in_repo='mashu_skins.tar',
            file_in_archive='.meta.json'
        ) == 8968
        assert hf_tar_file_size(
            repo_id='narugo/test_cos5t_tars',
            archive_in_repo='mashu_skins.tar',
            file_in_archive='愚人节_奥特瑙斯.png'
        ) == 255276
        assert hf_tar_file_size(
            repo_id='narugo/test_cos5t_tars',
            archive_in_repo='mashu_skins.tar',
            file_in_archive='./愚人节_奥特瑙斯.png'
        ) == 255276
        with pytest.raises(FileNotFoundError):
            _ = hf_tar_file_size(
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

    def test_hf_tar_file_download_small_exist(self):
        with isolated_directory({
            '.meta.json': get_testfile('skin_mashu', '.meta.json')
        }):
            hf_tar_file_download(
                repo_id='narugo/test_cos5t_tars',
                archive_in_repo='mashu_skins.tar',
                file_in_archive='.meta.json',
                local_file='.meta.json'
            )
            file_compare(get_testfile('skin_mashu', '.meta.json'), '.meta.json')

    def test_hf_tar_file_download_small_replace(self):
        with isolated_directory({
            '.meta.json': get_testfile('skin_mashu', '愚人节_奥特瑙斯.png')
        }):
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

    def test_hf_tar_file_download_lfs_exist(self):
        with isolated_directory({
            '愚人节_奥特瑙斯.png': get_testfile('skin_mashu', '愚人节_奥特瑙斯.png')
        }):
            hf_tar_file_download(
                repo_id='narugo/test_cos5t_tars',
                archive_in_repo='mashu_skins.tar',
                file_in_archive='./愚人节_奥特瑙斯.png',
                local_file='愚人节_奥特瑙斯.png'
            )
            file_compare(get_testfile('skin_mashu', '愚人节_奥特瑙斯.png'), '愚人节_奥特瑙斯.png')

    def test_hf_tar_file_download_lfs_replace(self):
        with isolated_directory({
            '愚人节_奥特瑙斯.png': get_testfile('skin_mashu', '.meta.json')
        }):
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

    def test_hf_tar_file_download_empty(self):
        with isolated_directory():
            hf_tar_file_download(
                repo_id='nyanko7/danbooru2023',
                idx_repo_id='deepghs/danbooru2023_index',
                archive_in_repo='original/data-0001.tar',
                file_in_archive='2946001.',
                local_file='2946001.',
            )
            assert os.path.getsize('2946001.') == 0

    def test_hf_tar_file_write_bytes_lfs_bytes(self):
        with isolated_directory(), io.BytesIO() as bf:
            hf_tar_file_write_bytes(
                repo_id='narugo/test_cos5t_tars',
                archive_in_repo='mashu_skins.tar',
                file_in_archive='./愚人节_奥特瑙斯.png',
                bin_file=bf,
            )
            assert bf.getvalue() == pathlib.Path(get_testfile('skin_mashu', '愚人节_奥特瑙斯.png')).read_bytes()

    def test_hf_tar_file_write_bytes_empty_bytes(self):
        with isolated_directory(), io.BytesIO() as bf:
            hf_tar_file_write_bytes(
                repo_id='nyanko7/danbooru2023',
                idx_repo_id='deepghs/danbooru2023_index',
                archive_in_repo='original/data-0001.tar',
                file_in_archive='2946001.',
                bin_file=bf
            )
            assert bf.getvalue() == b''

    def test_hf_tar_file_write_bytes_lfs_bytes_file(self):
        with isolated_directory():
            with open('愚人节_奥特瑙斯.png', 'wb') as bf:
                hf_tar_file_write_bytes(
                    repo_id='narugo/test_cos5t_tars',
                    archive_in_repo='mashu_skins.tar',
                    file_in_archive='./愚人节_奥特瑙斯.png',
                    bin_file=bf
                )
            file_compare(get_testfile('skin_mashu', '愚人节_奥特瑙斯.png'), '愚人节_奥特瑙斯.png')

    def test_hf_tar_file_write_bytes_empty_bytes_file(self):
        with isolated_directory():
            with open('2946001.', 'wb') as bf:
                hf_tar_file_write_bytes(
                    repo_id='nyanko7/danbooru2023',
                    idx_repo_id='deepghs/danbooru2023_index',
                    archive_in_repo='original/data-0001.tar',
                    file_in_archive='2946001.',
                    bin_file=bf
                )
            assert os.path.getsize('2946001.') == 0

    def test_hf_tar_file_write_bytes_not_found(self):
        with io.BytesIO() as bf, pytest.raises(FileNotFoundError):
            hf_tar_file_write_bytes(
                repo_id='narugo/test_cos5t_tars',
                archive_in_repo='mashu_skins.tar',
                file_in_archive='./愚人节奥特瑙斯.png',
                bin_file=bf,
            )

    def test_hf_tar_file_write_bytes_lfs_bytes_append(self):
        with isolated_directory(), io.BytesIO() as bf:
            bf.write(b'append_prefix_')
            hf_tar_file_write_bytes(
                repo_id='narugo/test_cos5t_tars',
                archive_in_repo='mashu_skins.tar',
                file_in_archive='./愚人节_奥特瑙斯.png',
                bin_file=bf,
            )
            assert bf.getvalue() == b'append_prefix_' + pathlib.Path(
                get_testfile('skin_mashu', '愚人节_奥特瑙斯.png')).read_bytes()

    def test_hf_tar_file_write_bytes_empty_bytes_append(self):
        with isolated_directory(), io.BytesIO() as bf:
            bf.write(b'append_prefix_')
            hf_tar_file_write_bytes(
                repo_id='nyanko7/danbooru2023',
                idx_repo_id='deepghs/danbooru2023_index',
                archive_in_repo='original/data-0001.tar',
                file_in_archive='2946001.',
                bin_file=bf
            )
            assert bf.getvalue() == b'append_prefix_'


@pytest.fixture
def mock_lru_cache():
    """Fixture to mock the LRUCache class and global variables."""
    mock_cache1 = MagicMock()
    mock_cache2 = MagicMock()

    with patch('hfutils.index.fetch._HF_TAR_IDX_CACHE', mock_cache1), \
            patch('hfutils.index.fetch._HF_TAR_IDX_PFILES_CACHE', mock_cache2), \
            patch('hfutils.index.fetch.LRUCache') as mock_lru:
        yield mock_cache1, mock_cache2, mock_lru


@pytest.mark.unittest
class TestHfTarCacheReset:
    def test_reset_without_maxsize(self, mock_lru_cache):
        """Test resetting the cache without changing the maxsize."""
        mock_cache1, mock_cache2, _ = mock_lru_cache

        hf_tar_cache_reset()

        mock_cache1.clear.assert_called_once()
        mock_cache2.clear.assert_called_once()

    def test_reset_with_same_maxsize(self, mock_lru_cache):
        """Test resetting the cache with the same maxsize."""
        mock_cache1, mock_cache2, mock_lru = mock_lru_cache
        mock_cache1.maxsize = 100

        hf_tar_cache_reset(maxsize=100)

        mock_cache1.clear.assert_called_once()
        mock_cache2.clear.assert_called_once()
        mock_lru.assert_not_called()

    def test_reset_with_different_maxsize(self, mock_lru_cache):
        """Test resetting the cache with a different maxsize."""
        mock_cache1, mock_cache2, mock_lru = mock_lru_cache
        mock_cache1.maxsize = 100

        hf_tar_cache_reset(maxsize=200)

        mock_cache1.clear.assert_called_once()
        mock_cache2.clear.assert_called_once()
        assert mock_lru.call_count == 2
        mock_lru.assert_called_with(maxsize=200)

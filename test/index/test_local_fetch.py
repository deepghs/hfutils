import io
import os.path
import pathlib
from unittest.mock import MagicMock, patch

import pytest
from hbutils.testing import isolated_directory
from natsort import natsorted

from hfutils.index import tar_list_files, tar_file_exists, tar_file_download, tar_file_info, \
    tar_file_size, tar_cache_reset, tar_file_write_bytes
from test.testings import get_testfile, file_compare


@pytest.mark.unittest
class TestIndexLocalFetch:
    def test_tar_list_files(self, local_narugo_test_cos5t_tars):
        files = tar_list_files(
            archive_file=os.path.join(local_narugo_test_cos5t_tars, 'mashu_skins.tar'),
        )
        assert len(files) == 17
        assert natsorted(files) == [
            '.meta.json', 'Bright_Voyager.png', 'Grail_League_1星.png', 'Grail_League_2星.png', 'Grail_League_3星.png',
            'Grail_League_4星.png', 'Grail_League_5星.png', '奥特瑙斯.png', '奥特瑙斯_改建型.png', '常夏的泳装.png',
            '常夏的泳装Ver_02.png', '愚人节.png', '愚人节_奥特瑙斯.png', '第1阶段.png', '第2阶段.png', '第3阶段.png',
            '第4阶段.png'
        ]

    def test_tar_file_exists(self, local_narugo_test_cos5t_tars):
        assert tar_file_exists(
            archive_file=os.path.join(local_narugo_test_cos5t_tars, 'mashu_skins.tar'),
            file_in_archive='.meta.json'
        )
        assert tar_file_exists(
            archive_file=os.path.join(local_narugo_test_cos5t_tars, 'mashu_skins.tar'),
            file_in_archive='愚人节_奥特瑙斯.png'
        )
        assert tar_file_exists(
            archive_file=os.path.join(local_narugo_test_cos5t_tars, 'mashu_skins.tar'),
            file_in_archive='./愚人节_奥特瑙斯.png'
        )
        assert not tar_file_exists(
            archive_file=os.path.join(local_narugo_test_cos5t_tars, 'mashu_skins.tar'),
            file_in_archive='愚人节奥特瑙斯.png'
        )

    def test_tar_file_info(self, local_narugo_test_cos5t_tars):
        assert tar_file_info(
            archive_file=os.path.join(local_narugo_test_cos5t_tars, 'mashu_skins.tar'),
            file_in_archive='.meta.json'
        ) == {
                   'offset': 2725376,
                   'sha256': '4585b01c251a496b73cb231d29fc711cfb1d682a84334d95f6f5b6c1cc5b5222',
                   'size': 8968
               }
        assert tar_file_info(
            archive_file=os.path.join(local_narugo_test_cos5t_tars, 'mashu_skins.tar'),
            file_in_archive='愚人节_奥特瑙斯.png'
        ) == {
                   'offset': 3954176,
                   'sha256': '991497fa586f6f4529827e0f8f1f228c20ec9fb507c314ee9d20d47c46f26e89',
                   'size': 255276
               }
        assert tar_file_info(
            archive_file=os.path.join(local_narugo_test_cos5t_tars, 'mashu_skins.tar'),
            file_in_archive='./愚人节_奥特瑙斯.png'
        ) == {
                   'offset': 3954176,
                   'sha256': '991497fa586f6f4529827e0f8f1f228c20ec9fb507c314ee9d20d47c46f26e89',
                   'size': 255276
               }
        with pytest.raises(FileNotFoundError):
            _ = tar_file_info(
                archive_file=os.path.join(local_narugo_test_cos5t_tars, 'mashu_skins.tar'),
                file_in_archive='愚人节奥特瑙斯.png'
            )

    def test_tar_file_size(self, local_narugo_test_cos5t_tars):
        assert tar_file_size(
            archive_file=os.path.join(local_narugo_test_cos5t_tars, 'mashu_skins.tar'),
            file_in_archive='.meta.json'
        ) == 8968
        assert tar_file_size(
            archive_file=os.path.join(local_narugo_test_cos5t_tars, 'mashu_skins.tar'),
            file_in_archive='愚人节_奥特瑙斯.png'
        ) == 255276
        assert tar_file_size(
            archive_file=os.path.join(local_narugo_test_cos5t_tars, 'mashu_skins.tar'),
            file_in_archive='./愚人节_奥特瑙斯.png'
        ) == 255276
        with pytest.raises(FileNotFoundError):
            _ = tar_file_size(
                archive_file=os.path.join(local_narugo_test_cos5t_tars, 'mashu_skins.tar'),
                file_in_archive='愚人节奥特瑙斯.png'
            )

    def test_tar_file_download_small(self, local_narugo_test_cos5t_tars):
        with isolated_directory():
            tar_file_download(
                archive_file=os.path.join(local_narugo_test_cos5t_tars, 'mashu_skins.tar'),
                file_in_archive='.meta.json',
                local_file='.meta.json'
            )
            file_compare(get_testfile('skin_mashu', '.meta.json'), '.meta.json')

    def test_tar_file_download_small_exist(self, local_narugo_test_cos5t_tars):
        with isolated_directory({
            '.meta.json': get_testfile('skin_mashu', '.meta.json')
        }):
            tar_file_download(
                archive_file=os.path.join(local_narugo_test_cos5t_tars, 'mashu_skins.tar'),
                file_in_archive='.meta.json',
                local_file='.meta.json'
            )
            file_compare(get_testfile('skin_mashu', '.meta.json'), '.meta.json')

    def test_tar_file_download_small_replace(self, local_narugo_test_cos5t_tars):
        with isolated_directory({
            '.meta.json': get_testfile('skin_mashu', '愚人节_奥特瑙斯.png')
        }):
            tar_file_download(
                archive_file=os.path.join(local_narugo_test_cos5t_tars, 'mashu_skins.tar'),
                file_in_archive='.meta.json',
                local_file='.meta.json'
            )
            file_compare(get_testfile('skin_mashu', '.meta.json'), '.meta.json')

    def test_tar_file_download_lfs(self, local_narugo_test_cos5t_tars):
        with isolated_directory():
            tar_file_download(
                archive_file=os.path.join(local_narugo_test_cos5t_tars, 'mashu_skins.tar'),
                file_in_archive='./愚人节_奥特瑙斯.png',
                local_file='愚人节_奥特瑙斯.png'
            )
            file_compare(get_testfile('skin_mashu', '愚人节_奥特瑙斯.png'), '愚人节_奥特瑙斯.png')

    def test_tar_file_download_lfs_exist(self, local_narugo_test_cos5t_tars):
        with isolated_directory({
            '愚人节_奥特瑙斯.png': get_testfile('skin_mashu', '愚人节_奥特瑙斯.png'),
        }):
            tar_file_download(
                archive_file=os.path.join(local_narugo_test_cos5t_tars, 'mashu_skins.tar'),
                file_in_archive='./愚人节_奥特瑙斯.png',
                local_file='愚人节_奥特瑙斯.png',
            )
            file_compare(get_testfile('skin_mashu', '愚人节_奥特瑙斯.png'), '愚人节_奥特瑙斯.png')

    def test_tar_file_download_lfs_replace(self, local_narugo_test_cos5t_tars):
        with isolated_directory({
            '愚人节_奥特瑙斯.png': get_testfile('skin_mashu', '.meta.json'),
        }):
            tar_file_download(
                archive_file=os.path.join(local_narugo_test_cos5t_tars, 'mashu_skins.tar'),
                file_in_archive='./愚人节_奥特瑙斯.png',
                local_file='愚人节_奥特瑙斯.png',
            )
            file_compare(get_testfile('skin_mashu', '愚人节_奥特瑙斯.png'), '愚人节_奥特瑙斯.png')

    def test_tar_file_download_not_found(self, local_narugo_test_cos5t_tars):
        with isolated_directory(), pytest.raises(FileNotFoundError):
            tar_file_download(
                archive_file=os.path.join(local_narugo_test_cos5t_tars, 'mashu_skins.tar'),
                file_in_archive='./愚人节奥特瑙斯.png',
                local_file='愚人节_奥特瑙斯.png'
            )

    def test_tar_file_download_subdir(self, local_narugo_test_cos5t_tars):
        with isolated_directory():
            tar_file_download(
                archive_file=os.path.join(local_narugo_test_cos5t_tars, 'ex3.tar'),
                file_in_archive='artoria_caster_third_ascension_fate/sankaku_21305298.jpg',
                local_file='f/ac.jpg'
            )
            file_compare(get_testfile('sankaku_21305298.jpg'), 'f/ac.jpg')

    def test_tar_file_download_empty(self, local_narugo_test_cos5t_tars):
        with isolated_directory():
            tar_file_download(
                archive_file=os.path.join(local_narugo_test_cos5t_tars, 'empty_file.tar'),
                file_in_archive='empty_file',
                local_file='empty_file',
            )
            assert os.path.getsize('empty_file') == 0

    def test_tar_file_write_bytes_small(self, local_narugo_test_cos5t_tars):
        with isolated_directory(), io.BytesIO() as wf:
            tar_file_write_bytes(
                archive_file=os.path.join(local_narugo_test_cos5t_tars, 'mashu_skins.tar'),
                file_in_archive='.meta.json',
                file=wf
            )
            assert wf.getvalue() == pathlib.Path(get_testfile('skin_mashu', '.meta.json')).read_bytes()

    def test_tar_file_write_bytes_small_exist(self, local_narugo_test_cos5t_tars):
        with isolated_directory({
            '.meta.json': get_testfile('skin_mashu', '.meta.json')
        }), io.BytesIO() as wf:
            tar_file_write_bytes(
                archive_file=os.path.join(local_narugo_test_cos5t_tars, 'mashu_skins.tar'),
                file_in_archive='.meta.json',
                file=wf
            )
            assert wf.getvalue() == pathlib.Path(get_testfile('skin_mashu', '.meta.json')).read_bytes()

    def test_tar_file_write_bytes_small_replace(self, local_narugo_test_cos5t_tars):
        with isolated_directory({
            '.meta.json': get_testfile('skin_mashu', '愚人节_奥特瑙斯.png')
        }), io.BytesIO() as wf:
            tar_file_write_bytes(
                archive_file=os.path.join(local_narugo_test_cos5t_tars, 'mashu_skins.tar'),
                file_in_archive='.meta.json',
                file=wf
            )
            assert wf.getvalue() == pathlib.Path(get_testfile('skin_mashu', '.meta.json')).read_bytes()

    def test_tar_file_write_bytes_lfs(self, local_narugo_test_cos5t_tars):
        with isolated_directory(), io.BytesIO() as wf:
            tar_file_write_bytes(
                archive_file=os.path.join(local_narugo_test_cos5t_tars, 'mashu_skins.tar'),
                file_in_archive='./愚人节_奥特瑙斯.png',
                file=wf
            )
            assert wf.getvalue() == pathlib.Path(get_testfile('skin_mashu', '愚人节_奥特瑙斯.png')).read_bytes()

    def test_tar_file_write_bytes_not_found(self, local_narugo_test_cos5t_tars):
        with isolated_directory(), io.BytesIO() as wf, pytest.raises(FileNotFoundError):
            tar_file_write_bytes(
                archive_file=os.path.join(local_narugo_test_cos5t_tars, 'mashu_skins.tar'),
                file_in_archive='./愚人节奥特瑙斯.png',
                file=wf
            )

    def test_tar_file_write_bytes_empty(self, local_narugo_test_cos5t_tars):
        with isolated_directory(), io.BytesIO() as wf:
            tar_file_write_bytes(
                archive_file=os.path.join(local_narugo_test_cos5t_tars, 'empty_file.tar'),
                file_in_archive='empty_file',
                file=wf
            )
            assert wf.tell() == 0
            assert wf.getvalue() == b''


@pytest.fixture
def mock_lru_cache():
    """Fixture to mock the LRUCache class and global variables."""
    mock_cache1 = MagicMock()
    mock_cache2 = MagicMock()

    with patch('hfutils.index.local_fetch._TAR_IDX_CACHE', mock_cache1), \
            patch('hfutils.index.local_fetch._TAR_IDX_PFILES_CACHE', mock_cache2), \
            patch('hfutils.index.local_fetch.LRUCache') as mock_lru:
        yield mock_cache1, mock_cache2, mock_lru


@pytest.mark.unittest
class TestTarCacheReset:
    def test_reset_without_maxsize(self, mock_lru_cache):
        """Test resetting the cache without changing the maxsize."""
        mock_cache1, mock_cache2, _ = mock_lru_cache

        tar_cache_reset()

        mock_cache1.clear.assert_called_once()
        mock_cache2.clear.assert_called_once()

    def test_reset_with_same_maxsize(self, mock_lru_cache):
        """Test resetting the cache with the same maxsize."""
        mock_cache1, mock_cache2, mock_lru = mock_lru_cache
        mock_cache1.maxsize = 100

        tar_cache_reset(maxsize=100)

        mock_cache1.clear.assert_called_once()
        mock_cache2.clear.assert_called_once()
        mock_lru.assert_not_called()

    def test_reset_with_different_maxsize(self, mock_lru_cache):
        """Test resetting the cache with a different maxsize."""
        mock_cache1, mock_cache2, mock_lru = mock_lru_cache
        mock_cache1.maxsize = 100

        tar_cache_reset(maxsize=200)

        mock_cache1.clear.assert_called_once()
        mock_cache2.clear.assert_called_once()
        assert mock_lru.call_count == 2
        mock_lru.assert_called_with(maxsize=200)

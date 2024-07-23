import os.path

import pytest

from hfutils.utils import hf_normpath, hf_fs_path, parse_hf_fs_path, HfFileSystemPath


@pytest.mark.unittest
class TestUtilsPath:
    def test_hf_normpath(self):
        assert hf_normpath('./1/2/3') == '1/2/3'
        assert hf_normpath('1/../2/3') == '2/3'
        assert hf_normpath('1///3') == '1/3'
        assert hf_normpath('1\\2/3') == '1/2/3'
        assert hf_normpath(os.path.join('1', '..', '2', '3', '4')) == '2/3/4'

    def test_hf_fs_path(self):
        assert hf_fs_path(
            repo_id='narugo/test_ds_repo',
            filename='1/2\\3'
        ) == 'datasets/narugo/test_ds_repo/1/2/3'
        assert hf_fs_path(
            repo_id='narugo/test_ds_repo',
            filename='1/2\\3',
            revision='main',
        ) == 'datasets/narugo/test_ds_repo@main/1/2/3'
        assert hf_fs_path(
            repo_id='narugo/test_ds_repo',
            repo_type='model',
            filename='1/2\\3',
            revision='r3',
        ) == 'narugo/test_ds_repo@r3/1/2/3'
        assert hf_fs_path(
            repo_id='narugo/test_ds_repo',
            repo_type='space',
            filename='1/2\\3',
            revision='r3',
        ) == 'spaces/narugo/test_ds_repo@r3/1/2/3'

    def test_parse_hf_fs_path(self):
        assert parse_hf_fs_path('datasets/narugo/test_ds_repo/1/2/3') == HfFileSystemPath(
            repo_id='narugo/test_ds_repo',
            filename='1/2/3',
            revision=None,
            repo_type='dataset',
        )
        assert parse_hf_fs_path('datasets/narugo/test_ds_repo@main/1/2/3') == HfFileSystemPath(
            repo_id='narugo/test_ds_repo',
            filename='1/2/3',
            revision='main',
            repo_type='dataset',
        )
        assert parse_hf_fs_path('narugo/test_ds_repo@r3/1/2/3') == HfFileSystemPath(
            repo_id='narugo/test_ds_repo',
            repo_type='model',
            filename='1/2/3',
            revision='r3',
        )
        assert parse_hf_fs_path('spaces/narugo/test_ds_repo@r3/1/2/3') == HfFileSystemPath(
            repo_id='narugo/test_ds_repo',
            repo_type='space',
            filename='1/2/3',
            revision='r3',
        )
        assert parse_hf_fs_path('spaces/narugo/test_ds_repo@refs/pr/10/1/2/3') == HfFileSystemPath(
            repo_id='narugo/test_ds_repo',
            repo_type='space',
            filename='1/2/3',
            revision='refs/pr/10',
        )
        # assert parse_hf_fs_path('datasets/imagenet-1k/classes.py') == HfFileSystemPath(
        #     repo_id='imagenet-1k',
        #     repo_type='dataset',
        #     filename='classes.py',
        #     revision=None,
        # )
        # assert parse_hf_fs_path('datasets/imagenet-1k@main/classes.py') == HfFileSystemPath(
        #     repo_id='imagenet-1k',
        #     repo_type='dataset',
        #     filename='classes.py',
        #     revision='main',
        # )
        assert parse_hf_fs_path('datasets/narugo/test_ds_repo') == HfFileSystemPath(
            repo_id='narugo/test_ds_repo',
            filename='.',
            revision=None,
            repo_type='dataset',
        )

    def test_parse_hf_fs_path_invalid(self):
        with pytest.raises(ValueError):
            _ = parse_hf_fs_path('datasets/narugo/test_ds_repo@@main/classes.py')

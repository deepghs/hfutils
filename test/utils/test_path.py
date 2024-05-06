import os.path

import pytest

from hfutils.utils import hf_normpath, hf_fs_path


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

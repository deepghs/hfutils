import pytest
from hbutils.testing import isolated_directory

from hfutils.operate import download_file_to_file
from test.testings import get_testfile, file_compare


@pytest.mark.unittest
class TestOperateDownloadXet:
    @pytest.mark.hf_git  # hf_xet is a native client: only a proxy sees what it says
    def test_download_file_to_file_xet(self, monkeypatch):
        from huggingface_hub import constants
        pytest.importorskip('hf_xet')
        if not hasattr(constants, 'HF_HUB_DISABLE_XET'):
            pytest.skip('this huggingface_hub has no Xet client')
        monkeypatch.setattr(constants, 'HF_HUB_DISABLE_XET', False)  # the suite turns Xet off, this test is about it

        with isolated_directory():
            download_file_to_file(
                'mashu_download.png',
                repo_id='deepghs/game_character_skins',
                file_in_repo='fgo/1/常夏的泳装Ver_02.png',
            )
            file_compare(get_testfile('mashu.png'), 'mashu_download.png')

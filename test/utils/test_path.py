import pytest

from hfutils.utils import hf_normpath


@pytest.mark.unittest
class TestUtilsPath:
    def test_hf_normpath(self):
        assert hf_normpath('./1/2/3') == '1/2/3'
        assert hf_normpath('1/../2/3') == '2/3'
        assert hf_normpath('1///3') == '1/3'
        assert hf_normpath('1\\2/3') == '1/2/3'

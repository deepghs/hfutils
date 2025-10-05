from unittest.mock import MagicMock, patch

import pytest

from hfutils.meta import hf_site_info, HfSiteInfo


@pytest.fixture
def mock_non_404_response():
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {'site': 'custom_site', 'version': '1.0.0'}
    return mock_response


@pytest.fixture
def mock_404_response():
    mock_response = MagicMock()
    mock_response.status_code = 404
    return mock_response


@pytest.mark.unittest
class TestMetaVersion:
    def test_hf_site_info(self):
        assert hf_site_info() == HfSiteInfo(site='huggingface')

    @patch('hfutils.meta.version.get_session')
    def test_hf_site_info_404_response(self, mock_get_session, mock_404_response):
        mock_session = MagicMock()
        mock_session.post.return_value = mock_404_response
        mock_get_session.return_value = mock_session

        assert hf_site_info() == HfSiteInfo(site='huggingface')

    @patch('hfutils.meta.version.get_session')
    def test_hf_site_info_non_404_response(self, mock_get_session, mock_non_404_response):
        mock_session = MagicMock()
        mock_session.post.return_value = mock_non_404_response
        mock_get_session.return_value = mock_session

        assert hf_site_info() == HfSiteInfo(site='custom_site', version='1.0.0')

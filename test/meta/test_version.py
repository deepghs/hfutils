from unittest.mock import MagicMock, patch

import pytest

from hfutils.meta import hf_site_info, HfSiteInfo


@pytest.fixture
def mock_non_401_response():
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {'name': 'MyCustomSite LOL', 'site': 'custom_site', 'version': '1.0.0'}
    return mock_response


@pytest.fixture
def mock_401_response():
    mock_response = MagicMock()
    mock_response.status_code = 401
    return mock_response


@pytest.mark.unittest
class TestMetaVersion:
    def test_hf_site_info(self):
        assert hf_site_info() == HfSiteInfo(
            name='HuggingFace (Official)',
            site='huggingface',
            version='official',
        )

    @patch('hfutils.meta.version.get_session')
    def test_hf_site_info_401_response(self, mock_get_session, mock_401_response):
        mock_session = MagicMock()
        mock_session.get.return_value = mock_401_response
        mock_get_session.return_value = mock_session

        assert hf_site_info() == HfSiteInfo(
            name='HuggingFace (Official)',
            site='huggingface',
            version='official',
        )

    @patch('hfutils.meta.version.get_session')
    def test_hf_site_info_401_response_custom(self, mock_get_session, mock_401_response):
        mock_session = MagicMock()
        mock_session.get.return_value = mock_401_response
        mock_get_session.return_value = mock_session

        assert hf_site_info(endpoint='https://hf.custom.co') == HfSiteInfo(
            name='HuggingFace (Custom Enterprise)',
            site='huggingface',
            version='custom',
        )

    @patch('hfutils.meta.version.get_session')
    def test_hf_site_info_non_401_response(self, mock_get_session, mock_non_401_response):
        mock_session = MagicMock()
        mock_session.get.return_value = mock_non_401_response
        mock_get_session.return_value = mock_session

        assert hf_site_info() == HfSiteInfo(
            name='MyCustomSite LOL',
            site='custom_site',
            version='1.0.0',
        )

from unittest.mock import patch, Mock

import pytest
import requests
from huggingface_hub import hf_hub_url
from requests.adapters import HTTPAdapter

from hfutils.utils.session import TimeoutHTTPAdapter, get_requests_session, get_random_ua


@pytest.fixture
def mock_requests_session():
    with patch('requests.session') as mock_session:
        yield mock_session.return_value


@pytest.fixture
def mock_ua_pool():
    with patch('hfutils.utils.session._ua_pool') as mock_pool:
        mock_pool.return_value.get_random_user_agent.return_value = 'MockUserAgent'
        yield mock_pool


@pytest.fixture()
def example_url():
    return hf_hub_url(
        repo_id='deepghs/danbooru_newest',
        repo_type='dataset',
        filename='README.md'
    )


@pytest.mark.unittest
class TestUtilsSession:
    def test_timeout_http_adapter_init(self, ):
        adapter = TimeoutHTTPAdapter()
        assert adapter.timeout == 15

        adapter = TimeoutHTTPAdapter(timeout=30)
        assert adapter.timeout == 30

    def test_timeout_http_adapter_send(self, ):
        adapter = TimeoutHTTPAdapter(timeout=10)
        mock_request = Mock()
        mock_kwargs = {}

        with patch.object(HTTPAdapter, 'send') as mock_send:
            adapter.send(mock_request, **mock_kwargs)
            mock_send.assert_called_once_with(mock_request, timeout=10)

        mock_kwargs = {'timeout': 20}
        with patch.object(HTTPAdapter, 'send') as mock_send:
            adapter.send(mock_request, **mock_kwargs)
            mock_send.assert_called_once_with(mock_request, timeout=20)

    def test_get_requests_session(self, mock_ua_pool):
        session = get_requests_session()
        assert isinstance(session, requests.Session)
        assert 'User-Agent' in session.headers
        assert session.headers['User-Agent'] == 'MockUserAgent'

        custom_headers = {'Custom-Header': 'Value'}
        session = get_requests_session(headers=custom_headers)
        assert 'Custom-Header' in session.headers
        assert session.headers['Custom-Header'] == 'Value'

        session = get_requests_session(verify=False)
        assert session.verify is False

        existing_session = requests.Session()
        session = get_requests_session(session=existing_session)
        assert session is existing_session

    def test_get_requests_session_with_custom_params(self):
        session = get_requests_session(max_retries=3, timeout=30)
        assert isinstance(session, requests.Session)
        # You might want to add more assertions here to check if the custom parameters are applied correctly

    def test_get_random_ua(self, mock_ua_pool):
        ua = get_random_ua()
        assert ua == 'MockUserAgent'
        mock_ua_pool.return_value.get_random_user_agent.assert_called_once()

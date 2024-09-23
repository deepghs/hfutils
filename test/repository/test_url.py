from unittest.mock import patch

import pytest

from hfutils.repository import hf_hub_repo_path_url, hf_hub_repo_file_url


# Fixtures
@pytest.fixture
def mock_hf_hub_repo_url():
    with patch('hfutils.repository.url.hf_hub_repo_url') as mock:
        mock.return_value = 'https://huggingface.co/repo'
        yield mock


@pytest.fixture
def mock_hf_normpath():
    with patch('hfutils.repository.url.hf_normpath') as mock:
        mock.side_effect = lambda x: x
        yield mock


@pytest.mark.unittest
class TestHuggingFaceHubUrls:
    def test_hf_hub_repo_path_url_default(self, mock_hf_hub_repo_url, mock_hf_normpath):
        result = hf_hub_repo_path_url('user/repo', 'path/to/file')
        assert result == 'https://huggingface.co/repo/tree/main/path/to/file'
        mock_hf_hub_repo_url.assert_called_once_with(repo_id='user/repo', repo_type='dataset', endpoint=None)

    def test_hf_hub_repo_path_url_custom(self, mock_hf_hub_repo_url, mock_hf_normpath):
        result = hf_hub_repo_path_url('user/repo', 'path/to/file', repo_type='model', revision='dev',
                                      endpoint='https://custom.com')
        assert result == 'https://huggingface.co/repo/tree/dev/path/to/file'
        mock_hf_hub_repo_url.assert_called_once_with(repo_id='user/repo', repo_type='model',
                                                     endpoint='https://custom.com')

    def test_hf_hub_repo_path_url_special_chars(self, mock_hf_hub_repo_url, mock_hf_normpath):
        result = hf_hub_repo_path_url('user/repo', 'path/to/file with spaces', revision='branch/with/slashes')
        assert result == 'https://huggingface.co/repo/tree/branch%2Fwith%2Fslashes/path/to/file with spaces'

    def test_hf_hub_repo_file_url_default(self, mock_hf_hub_repo_url, mock_hf_normpath):
        result = hf_hub_repo_file_url('user/repo', 'path/to/file')
        assert result == 'https://huggingface.co/repo/blob/main/path/to/file'
        mock_hf_hub_repo_url.assert_called_once_with(repo_id='user/repo', repo_type='dataset', endpoint=None)

    def test_hf_hub_repo_file_url_custom(self, mock_hf_hub_repo_url, mock_hf_normpath):
        result = hf_hub_repo_file_url('user/repo', 'path/to/file', repo_type='model', revision='dev',
                                      endpoint='https://custom.com')
        assert result == 'https://huggingface.co/repo/blob/dev/path/to/file'
        mock_hf_hub_repo_url.assert_called_once_with(repo_id='user/repo', repo_type='model',
                                                     endpoint='https://custom.com')

    def test_hf_hub_repo_file_url_special_chars(self, mock_hf_hub_repo_url, mock_hf_normpath):
        result = hf_hub_repo_file_url('user/repo', 'path/to/file with spaces', revision='branch/with/slashes')
        assert result == 'https://huggingface.co/repo/blob/branch%2Fwith%2Fslashes/path/to/file with spaces'

    def test_hf_hub_repo_path_url_default_x(self):
        result = hf_hub_repo_path_url('user/repo', 'path/to/file')
        expected = f"https://huggingface.co/datasets/user/repo/tree/main/path/to/file"
        assert result == expected

    def test_hf_hub_repo_path_url_model(self):
        result = hf_hub_repo_path_url('user/repo', 'path/to/file', repo_type='model')
        expected = f"https://huggingface.co/user/repo/tree/main/path/to/file"
        assert result == expected

    def test_hf_hub_repo_path_url_space(self):
        result = hf_hub_repo_path_url('user/repo', 'path/to/file', repo_type='space')
        expected = f"https://huggingface.co/spaces/user/repo/tree/main/path/to/file"
        assert result == expected

    def test_hf_hub_repo_path_url_custom_revision(self):
        result = hf_hub_repo_path_url('user/repo', 'path/to/file', revision='v1.0')
        expected = f"https://huggingface.co/datasets/user/repo/tree/v1.0/path/to/file"
        assert result == expected

    def test_hf_hub_repo_path_url_custom_endpoint(self):
        result = hf_hub_repo_path_url('user/repo', 'path/to/file', endpoint='https://custom.com')
        expected = f"https://custom.com/datasets/user/repo/tree/main/path/to/file"
        assert result == expected

    def test_hf_hub_repo_file_url_default(self):
        result = hf_hub_repo_file_url('user/repo', 'path/to/file')
        expected = f"https://huggingface.co/datasets/user/repo/blob/main/path/to/file"
        assert result == expected

    def test_hf_hub_repo_file_url_model(self):
        result = hf_hub_repo_file_url('user/repo', 'path/to/file', repo_type='model')
        expected = f"https://huggingface.co/user/repo/blob/main/path/to/file"
        assert result == expected

    def test_hf_hub_repo_file_url_space(self):
        result = hf_hub_repo_file_url('user/repo', 'path/to/file', repo_type='space')
        expected = f"https://huggingface.co/spaces/user/repo/blob/main/path/to/file"
        assert result == expected

    def test_hf_hub_repo_file_url_custom_revision(self):
        result = hf_hub_repo_file_url('user/repo', 'path/to/file', revision='v1.0')
        expected = f"https://huggingface.co/datasets/user/repo/blob/v1.0/path/to/file"
        assert result == expected

    def test_hf_hub_repo_file_url_custom_endpoint(self):
        result = hf_hub_repo_file_url('user/repo', 'path/to/file', endpoint='https://custom.com')
        expected = f"https://custom.com/datasets/user/repo/blob/main/path/to/file"
        assert result == expected

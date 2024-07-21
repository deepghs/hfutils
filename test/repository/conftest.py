import shutil
from unittest.mock import patch

import pytest

_o_shutil_which = shutil.which


def _fake_git_info_no_git(*args, **kwargs):
    _ = args, kwargs
    return {
        'exec': None,
        'installed': False,
    }


@pytest.fixture()
def no_git():
    with patch('hfutils.repository.base.git_info', _fake_git_info_no_git):
        yield


def _fake_git_info_no_lfs(*args, **kwargs):
    _ = args, kwargs
    return {
        'exec': shutil.which('git'),
        'installed': True,
        'version': '2.28.0',
        'version_info': 'git version 2.28.0',
        'lfs': {
            'installed': False,
        }
    }


@pytest.fixture()
def no_lfs():
    with patch('hfutils.repository.base.git_info', _fake_git_info_no_lfs):
        yield

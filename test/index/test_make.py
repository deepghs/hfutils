import json

import pytest
from hbutils.testing import isolated_directory

from hfutils.index import tar_get_index_info, tar_create_index
from test.testings import get_testfile


@pytest.fixture()
def raw_tar():
    return get_testfile('raw.tar')


@pytest.mark.unittest
class TestIndexMake:
    def test_tar_get_index_info(self, raw_tar):
        assert tar_get_index_info(raw_tar) == {
            'files': {
                '1.txt': {
                    'offset': 3584,
                    'sha256': '57a67d463dde06dcf3bf3bd8382ebf5c8d6e0a854135914e215f09fc0e1080b9',
                    'size': 13
                },
                'README.md': {
                    'offset': 1536,
                    'sha256': '75fae9f83087725e606ed7bf243a6655b1ddf583919529b3291980322b62af77',
                    'size': 51
                },
                'subdir/script.py': {
                    'offset': 5632,
                    'sha256': '5c3086e72529e59e42002f11bbfabc40b084981daedb1a3d4a31623122fd8867',
                    'size': 33
                }
            },
            'filesize': 10240,
            'hash': '55d6e39981cd94f0d9732b40ff677a508d6652a1',
            'hash_lfs': 'be9ae98f74065d2df47f38263644941532b6615b5a60c34db8cc864b4ade147a'
        }

    def test_tar_create_index(self, raw_tar):
        with isolated_directory({'raw.tar': raw_tar}):
            tar_create_index('raw.tar')
            with open('raw.json', 'r') as f:
                assert json.load(f) == {
                    'files': {
                        '1.txt': {
                            'offset': 3584,
                            'sha256': '57a67d463dde06dcf3bf3bd8382ebf5c8d6e0a854135914e215f09fc0e1080b9',
                            'size': 13
                        },
                        'README.md': {
                            'offset': 1536,
                            'sha256': '75fae9f83087725e606ed7bf243a6655b1ddf583919529b3291980322b62af77',
                            'size': 51
                        },
                        'subdir/script.py': {
                            'offset': 5632,
                            'sha256': '5c3086e72529e59e42002f11bbfabc40b084981daedb1a3d4a31623122fd8867',
                            'size': 33
                        }
                    },
                    'filesize': 10240,
                    'hash': '55d6e39981cd94f0d9732b40ff677a508d6652a1',
                    'hash_lfs': 'be9ae98f74065d2df47f38263644941532b6615b5a60c34db8cc864b4ade147a'
                }

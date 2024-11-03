import os.path

import pytest

from hfutils.utils import walk_files


@pytest.fixture()
def src_config_dir():
    return os.path.join('hfutils', 'config')


@pytest.fixture()
def src_dir():
    return 'hfutils'


@pytest.mark.unittest
class TestUtilsWalk:
    def test_walk_files(self, src_config_dir, src_dir):
        files = set(walk_files(src_config_dir))
        assert 'meta.py' in files
        assert '__init__.py' in files

        files = set(walk_files(src_dir))
        assert os.path.join('config', 'meta.py') in files
        assert os.path.join('config', '__init__.py') in files
        assert os.path.join('index', '__init__.py') in files

    def test_walk_files_with_pattern(self, src_config_dir, src_dir):
        files = set(walk_files(src_config_dir, pattern='__*__.py'))
        assert 'meta.py' not in files
        assert '__init__.py' in files

        files = set(walk_files(src_dir, pattern='config/**/*'))
        assert os.path.join('config', 'meta.py') in files
        assert os.path.join('config', '__init__.py') in files
        assert os.path.join('index', '__init__.py') not in files

        files = set(walk_files(src_dir, pattern='**/__init__.py'))
        assert os.path.join('config', 'meta.py') not in files
        assert os.path.join('config', '__init__.py') in files
        assert os.path.join('index', '__init__.py') in files

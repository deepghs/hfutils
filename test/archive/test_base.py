import os

import pytest
from hbutils.testing import isolated_directory, disable_output

from hfutils.archive import get_archive_type, get_archive_extname, archive_pack, register_archive_type


@pytest.mark.unittest
class TestArchiveBase:
    def test_get_archive_type(self):
        assert get_archive_type(os.path.join('1.zip')) == 'zip'
        assert get_archive_type(os.path.join('111', 'f.zip')) == 'zip'

        with pytest.raises(ValueError):
            _ = get_archive_type('1.mp3')
        with pytest.raises(ValueError):
            _ = get_archive_type('')

    def test_get_archive_extname(self):
        assert get_archive_extname('zip') == '.zip'
        with pytest.raises(ValueError):
            _ = get_archive_extname('mp3')
        with pytest.raises(ValueError):
            _ = get_archive_extname('')

    def test_pack_with_warning(self, raw_dir):
        with isolated_directory():
            with pytest.warns(None), disable_output():
                archive_pack('zip', raw_dir, 'file.zip')
            with pytest.warns(UserWarning), disable_output():
                archive_pack('zip', raw_dir, 'file.mp3')

    def test_empty_register(self):
        with pytest.raises(ValueError):
            register_archive_type('xxx', [], lambda: None, lambda: None)

import os
from enum import Enum
from unittest.mock import patch

import pytest

from hfutils.utils import FileItemType, get_file_type


@pytest.mark.unittest
class TestUtilsType:
    def test_list_item_type_enum(self):
        assert isinstance(FileItemType.FILE, Enum)
        assert FileItemType.FILE.value == 0x1
        assert FileItemType.FOLDER.value == 0x2
        assert FileItemType.IMAGE.value == 0x3
        assert FileItemType.ARCHIVE.value == 0x4
        assert FileItemType.MODEL.value == 0x5
        assert FileItemType.DATA.value == 0x6

    @pytest.mark.parametrize("item_type, expected_color", [
        (FileItemType.FILE, None),
        (FileItemType.FOLDER, 'blue'),
        (FileItemType.IMAGE, 'magenta'),
        (FileItemType.ARCHIVE, 'red'),
        (FileItemType.MODEL, 'green'),
        (FileItemType.DATA, 'yellow'),
    ])
    def test_render_color(self, item_type, expected_color):
        assert item_type.render_color == expected_color

    def test_render_color_unknown_type(self):
        class UnknownType(Enum):
            UNKNOWN = 0x7

        with pytest.raises(ValueError, match='Unknown type'):
            FileItemType.render_color.fget(UnknownType.UNKNOWN)

    @pytest.mark.parametrize("filename, expected_type", [
        ('file.txt', FileItemType.FILE),
        ('image.jpg', FileItemType.IMAGE),
        ('archive.zip', FileItemType.ARCHIVE),
        ('model.pkl', FileItemType.MODEL),
        ('data.csv', FileItemType.DATA),
        ('folder', FileItemType.FILE),  # Assuming folders are not detected by filename
    ])
    def test_get_file_type(self, filename, expected_type):
        with patch('mimetypes.guess_type') as mock_guess_type, \
                patch('hfutils.utils.type_.is_archive_or_compressed') as mock_is_archive, \
                patch('hfutils.utils.type_.is_model_file') as mock_is_model, \
                patch('hfutils.utils.type_.is_data_file') as mock_is_data:
            mock_guess_type.return_value = (None, None)
            mock_is_archive.return_value = expected_type == FileItemType.ARCHIVE
            mock_is_model.return_value = expected_type == FileItemType.MODEL
            mock_is_data.return_value = expected_type == FileItemType.DATA

            if expected_type == FileItemType.IMAGE:
                mock_guess_type.return_value = ('image/jpeg', None)

            assert get_file_type(filename) == expected_type

    def test_get_file_type_with_path(self):
        with patch('mimetypes.guess_type') as mock_guess_type:
            mock_guess_type.return_value = (None, None)
            assert get_file_type('/path/to/file.txt') == FileItemType.FILE

    def test_get_file_type_invalid_input(self):
        with pytest.raises(TypeError, match='Unknown file name type'):
            get_file_type(123)

    def test_get_file_type_empty_string(self):
        with patch('mimetypes.guess_type') as mock_guess_type:
            mock_guess_type.return_value = (None, None)
            assert get_file_type('') == FileItemType.FILE

    @pytest.mark.parametrize("filename", [
        'file.txt', 'FILE.TXT', 'FiLe.TxT',
        '/path/to/file.txt',
        r'C:\path\to\file.txt',
    ])
    def test_get_file_type_case_insensitive(self, filename):
        with patch('mimetypes.guess_type') as mock_guess_type:
            mock_guess_type.return_value = (None, None)
            assert get_file_type(filename) == FileItemType.FILE

    def test_get_file_type_with_pathlike_object(self):
        with patch('mimetypes.guess_type') as mock_guess_type:
            mock_guess_type.return_value = (None, None)
            path = os.path.join('path', 'to', 'file.txt')
            assert get_file_type(os.fspath(path)) == FileItemType.FILE

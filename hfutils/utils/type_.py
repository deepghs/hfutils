"""
This module provides functionality for determining file types and managing list item types.

It includes an enumeration class for different types of list items, and a function to determine
the type of a given file. The module also adds support for the WebP image format.

The module uses the ``mimetypes`` library for MIME type detection and imports custom functions
for identifying archive, model, and data files.
"""

import mimetypes
import os
from enum import Enum, unique
from typing import Union

from .archive import is_archive_or_compressed
from .data import is_data_file
from .model import is_model_file

mimetypes.add_type('image/webp', '.webp')


@unique
class FileItemType(Enum):
    """
    Enum class representing different types of list items.

    This enumeration defines various file and folder types that can be encountered
    in a file system or list of items. Each type is associated with a unique integer value.

    Usage:
        >>> item_type = FileItemType.FILE
        >>> print(item_type)
        FileItemType.FILE
        >>> print(item_type.value)
        1
    """

    FILE = 0x1
    FOLDER = 0x2
    IMAGE = 0x3
    ARCHIVE = 0x4
    MODEL = 0x5
    DATA = 0x6

    @property
    def render_color(self):
        """
        Get the render color based on the item type.

        This property returns a color string associated with each item type,
        which can be used for rendering or display purposes.

        :return: The render color for the item type.
        :rtype: str or None

        :raises ValueError: If an unknown item type is encountered.

        Usage:
            >>> item_type = FileItemType.FOLDER
            >>> print(item_type.render_color)
            blue
        """
        if self == FileItemType.FILE:
            return None
        elif self == FileItemType.FOLDER:
            return 'blue'
        elif self == FileItemType.IMAGE:
            return 'magenta'
        elif self == FileItemType.ARCHIVE:
            return 'red'
        elif self == FileItemType.MODEL:
            return 'green'
        elif self == FileItemType.DATA:
            return 'yellow'
        else:
            raise ValueError(f'Unknown type - {self!r}')  # pragma: no cover


def get_file_type(filename: Union[str, os.PathLike]) -> FileItemType:
    """
    Determine the type of a given file.

    This function analyzes the provided filename and returns the corresponding FileItemType.
    It uses various methods to determine the file type, including checking for archives,
    model files, data files, and image files based on MIME types.

    :param filename: The name or path of the file to analyze.
    :type filename: Union[str, os.PathLike]

    :return: The determined FileItemType for the given file.
    :rtype: FileItemType

    :raises TypeError: If the provided filename is not a string or PathLike object.

    Usage:
        >>> file_type = get_file_type('image.jpg')
        >>> print(file_type)
        FileItemType.IMAGE

        >>> file_type = get_file_type('data.csv')
        >>> print(file_type)
        FileItemType.DATA
    """
    if not isinstance(filename, (str, os.PathLike)):
        raise TypeError(f'Unknown file name type - {filename!r}')
    filename = os.path.basename(os.path.normcase(str(filename)))

    mimetype, _ = mimetypes.guess_type(filename)
    type_ = FileItemType.FILE
    if is_archive_or_compressed(filename):
        type_ = FileItemType.ARCHIVE
    elif is_model_file(filename):
        type_ = FileItemType.MODEL
    elif is_data_file(filename):
        type_ = FileItemType.DATA
    elif mimetype:
        if 'image' in mimetype:
            type_ = FileItemType.IMAGE

    return type_

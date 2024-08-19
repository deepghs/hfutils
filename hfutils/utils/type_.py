import mimetypes
import os
from enum import Enum, unique
from typing import Union

from .archive import is_archive_or_compressed

mimetypes.add_type('image/webp', '.webp')


@unique
class ListItemType(Enum):
    """
    Enum class representing different types of list items.
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

        :return: The render color for the item type.
        :rtype: str
        """
        if self == self.FILE:
            return None
        elif self == self.FOLDER:
            return 'blue'
        elif self == self.IMAGE:
            return 'magenta'
        elif self == self.ARCHIVE:
            return 'red'
        elif self == self.MODEL:
            return 'green'
        elif self == self.DATA:
            return 'yellow'
        else:
            raise ValueError(f'Unknown type - {self!r}')  # pragma: no cover


def get_file_type(filename: Union[str, os.PathLike]) -> ListItemType:
    if not isinstance(filename, (str, os.PathLike)):
        raise TypeError(f'Unknown file name type - {filename!r}')
    filename = os.path.basename(os.path.normcase(str(filename)))

    mimetype, _ = mimetypes.guess_type(filename)
    _, ext = os.path.splitext(filename)
    type_ = ListItemType.FILE
    if is_archive_or_compressed(filename):
        type_ = ListItemType.ARCHIVE
    elif ext in {'.ckpt', '.pt', '.safetensors', '.onnx', '.model', '.h5', '.mlmodel',
                 '.ftz', '.pb', '.pth', '.tflite'}:
        type_ = ListItemType.MODEL
    elif ext in {'.json', '.csv', '.tsv', '.arrow', '.bin', '.msgpack', '.npy', '.npz',
                 '.parquet', '.pickle', '.pkl', '.wasm'}:
        type_ = ListItemType.DATA
    elif mimetype:
        if 'image' in mimetype:
            type_ = ListItemType.IMAGE

    return type_

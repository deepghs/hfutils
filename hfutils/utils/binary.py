"""
This module provides functionality to determine whether a given file is a binary file or a text file.
It does so by reading the first 1024 bytes of the file and checking for the presence of non-text characters.

.. note::
    Inspired from https://stackoverflow.com/a/7392391/6995899
"""

_TEXT_CHARS = bytearray({7, 8, 9, 10, 12, 13, 27} | set(range(0x20, 0x100)) - {0x7f})


def is_binary_file(file) -> bool:
    """
    Check if a given file is binary.

    This function reads the first 1024 bytes of the file and checks if it contains any
    non-text (binary) characters. It uses a predefined set of text characters to determine
    the nature of the file.

    :param file: The path to the file to be checked.
    :type file: str

    :return: True if the file is binary, False if it is a text file.
    :rtype: bool

    :raises FileNotFoundError: If the specified file does not exist.
    :raises IOError: If there is an error reading the file.

    :example:

    >>> is_binary_file('example.txt')
    False
    >>> is_binary_file('example.bin')
    True
    """
    with open(file, 'rb') as f:
        prefix = f.read(1024)
        return bool(prefix.translate(None, _TEXT_CHARS))

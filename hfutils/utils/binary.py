# Inspired from https://stackoverflow.com/a/7392391/6995899
_TEXT_CHARS = bytearray({7, 8, 9, 10, 12, 13, 27} | set(range(0x20, 0x100)) - {0x7f})


def is_binary_file(file) -> bool:
    """
    Check if a given file is binary.

    This function reads the first 1024 bytes of the file and checks if it contains any
    non-text (binary) characters.

    :param file: The path to the file to be checked.
    :type file: str

    :return: True if the file is binary, False if it is a text file.
    :rtype: bool
    """
    with open(file, 'rb') as f:
        prefix = f.read(1024)
        return bool(prefix.translate(None, _TEXT_CHARS))

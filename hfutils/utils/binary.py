# Inspired from https://stackoverflow.com/a/7392391/6995899
_TEXT_CHARS = bytearray({7, 8, 9, 10, 12, 13, 27} | set(range(0x20, 0x100)) - {0x7f})


def is_binary_file(file) -> bool:
    with open(file, 'rb') as f:
        prefix = f.read(1024)
        return bool(prefix.translate(None, _TEXT_CHARS))

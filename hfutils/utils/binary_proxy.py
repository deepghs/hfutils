from io import UnsupportedOperation
from typing import BinaryIO

from hbutils.testing import isolated_directory


class BinaryProxyIO(BinaryIO):
    def __init__(self, stream: BinaryIO):
        self._stream = stream
        self._pos = 0
        self._closed = False

    def __enter__(self):
        if self._closed:
            raise ValueError("I/O operation on closed file.")
        return self

    def close(self):
        self._closed = True
        self._after_close()

    def _after_close(self):
        pass

    def fileno(self):
        raise UnsupportedOperation("fileno")

    def flush(self):
        if self._closed:
            raise ValueError("I/O operation on closed file.")
        raise UnsupportedOperation("flush")

    def isatty(self):
        if self._closed:
            raise ValueError("I/O operation on closed file.")
        return False

    def read(self, __n=...):
        if self._closed:
            raise ValueError("I/O operation on closed file.")
        raise UnsupportedOperation("read")

    def readable(self):
        if self._closed:
            raise ValueError("I/O operation on closed file.")
        return False

    def readline(self, __limit=...):
        if self._closed:
            raise ValueError("I/O operation on closed file.")
        raise UnsupportedOperation("readline")

    def readlines(self, __hint=...):
        if self._closed:
            raise ValueError("I/O operation on closed file.")
        raise UnsupportedOperation("readlines")

    def seek(self, __offset, __whence=...):
        if self._closed:
            raise ValueError("I/O operation on closed file.")
        raise UnsupportedOperation("seek")

    def seekable(self):
        if self._closed:
            raise ValueError("I/O operation on closed file.")
        return False

    def tell(self):
        if self._closed:
            raise ValueError("I/O operation on closed file.")
        return self._pos

    def truncate(self, __size=...):
        if self._closed:
            raise ValueError("I/O operation on closed file.")
        raise UnsupportedOperation("truncate")

    def writable(self):
        if self._closed:
            raise ValueError("I/O operation on closed file.")
        return True

    def write(self, __s):
        if self._closed:
            raise ValueError("I/O operation on closed file.")
        self._stream.write(__s)
        self._pos += len(__s)
        self._on_write(__s)
        return len(__s)

    def _on_write(self, __s):
        pass

    def writelines(self, __lines):
        if self._closed:
            raise ValueError("I/O operation on closed file.")
        for line in __lines:
            self.write(line)

    def __next__(self):
        if self._closed:
            raise ValueError("I/O operation on closed file.")
        raise UnsupportedOperation("__next__")

    def __iter__(self):
        if self._closed:
            raise ValueError("I/O operation on closed file.")
        return self

    def __exit__(self, __t, __value, __traceback):
        self.close()

isolated_directory
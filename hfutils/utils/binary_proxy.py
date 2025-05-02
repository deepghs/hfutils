"""
BinaryProxyIO module provides a proxy implementation for binary I/O operations.

This module defines a class that wraps a binary stream and implements the BinaryIO interface,
primarily focusing on write operations while providing stubs for other operations.
It can be used as a base class for implementing custom binary I/O handlers that need
to intercept or modify write operations.
"""

from io import UnsupportedOperation
from typing import BinaryIO


class BinaryProxyIO(BinaryIO):
    """
    A proxy class that implements the BinaryIO interface, wrapping another binary stream.

    This class primarily supports write operations, while other operations raise
    :class:`io.UnsupportedOperation` exceptions by default. It can be extended by overriding
    the ``_on_write`` and ``_after_close`` methods to implement custom behavior.

    :param stream: The binary stream to wrap
    :type stream: BinaryIO
    """

    def __init__(self, stream: BinaryIO):
        """
        Initialize the proxy with a binary stream.

        :param stream: The binary stream to wrap
        :type stream: BinaryIO
        """
        self._stream = stream
        self._pos = 0
        self._closed = False

    def __enter__(self):
        """
        Enter the runtime context related to this object.

        :return: Self
        :rtype: BinaryProxyIO
        :raises ValueError: If the file is already closed
        """
        if self._closed:
            raise ValueError("I/O operation on closed file.")
        return self

    def close(self):
        """
        Close the file.

        This method sets the internal closed flag to True and calls _after_close.
        """
        self._closed = True
        self._after_close()

    def _after_close(self):
        """
        Hook method called after closing the file.

        This method can be overridden in subclasses to implement custom behavior
        when the file is closed.
        """
        pass

    def fileno(self):
        """
        Return the underlying file descriptor.

        :raises UnsupportedOperation: Always, as this operation is not supported
        """
        raise UnsupportedOperation("fileno")

    def flush(self):
        """
        Flush the write buffers.

        :raises ValueError: If the file is closed
        :raises UnsupportedOperation: Always, as this operation is not supported
        """
        if self._closed:
            raise ValueError("I/O operation on closed file.")
        raise UnsupportedOperation("flush")

    def isatty(self):
        """
        Return whether this is an 'interactive' stream.

        :return: Always False
        :rtype: bool
        :raises ValueError: If the file is closed
        """
        if self._closed:
            raise ValueError("I/O operation on closed file.")
        return False

    def read(self, __n=...):
        """
        Read up to n bytes from the object and return them.

        :param __n: Number of bytes to read
        :type __n: int, optional
        :raises ValueError: If the file is closed
        :raises UnsupportedOperation: Always, as this operation is not supported
        """
        if self._closed:
            raise ValueError("I/O operation on closed file.")
        raise UnsupportedOperation("read")

    def readable(self):
        """
        Return whether the file is readable.

        :return: Always False
        :rtype: bool
        :raises ValueError: If the file is closed
        """
        if self._closed:
            raise ValueError("I/O operation on closed file.")
        return False

    def readline(self, __limit=...):
        """
        Read and return one line from the stream.

        :param __limit: Maximum number of bytes to read
        :type __limit: int, optional
        :raises ValueError: If the file is closed
        :raises UnsupportedOperation: Always, as this operation is not supported
        """
        if self._closed:
            raise ValueError("I/O operation on closed file.")
        raise UnsupportedOperation("readline")

    def readlines(self, __hint=...):
        """
        Return a list of lines from the stream.

        :param __hint: Maximum number of bytes to read
        :type __hint: int, optional
        :raises ValueError: If the file is closed
        :raises UnsupportedOperation: Always, as this operation is not supported
        """
        if self._closed:
            raise ValueError("I/O operation on closed file.")
        raise UnsupportedOperation("readlines")

    def seek(self, __offset, __whence=...):
        """
        Change the stream position.

        :param __offset: Offset relative to position indicated by whence
        :type __offset: int
        :param __whence: Position from which offset is applied
        :type __whence: int, optional
        :raises ValueError: If the file is closed
        :raises UnsupportedOperation: Always, as this operation is not supported
        """
        if self._closed:
            raise ValueError("I/O operation on closed file.")
        raise UnsupportedOperation("seek")

    def seekable(self):
        """
        Return whether the file supports seeking.

        :return: Always False
        :rtype: bool
        :raises ValueError: If the file is closed
        """
        if self._closed:
            raise ValueError("I/O operation on closed file.")
        return False

    def tell(self):
        """
        Return the current stream position.

        :return: Current position in the file
        :rtype: int
        :raises ValueError: If the file is closed
        """
        if self._closed:
            raise ValueError("I/O operation on closed file.")
        return self._pos

    def truncate(self, __size=...):
        """
        Truncate the file to at most size bytes.

        :param __size: Size to truncate to
        :type __size: int, optional
        :raises ValueError: If the file is closed
        :raises UnsupportedOperation: Always, as this operation is not supported
        """
        if self._closed:
            raise ValueError("I/O operation on closed file.")
        raise UnsupportedOperation("truncate")

    def writable(self):
        """
        Return whether the file is writable.

        :return: Always True
        :rtype: bool
        :raises ValueError: If the file is closed
        """
        if self._closed:
            raise ValueError("I/O operation on closed file.")
        return True

    def write(self, __s):
        """
        Write bytes to the file.

        This method writes the bytes to the wrapped stream, updates the position,
        calls the _on_write hook, and returns the number of bytes written.

        :param __s: Bytes to write
        :type __s: bytes
        :return: Number of bytes written
        :rtype: int
        :raises ValueError: If the file is closed
        """
        if self._closed:
            raise ValueError("I/O operation on closed file.")
        self._stream.write(__s)
        self._pos += len(__s)
        self._on_write(__s)
        return len(__s)

    def _on_write(self, __s):
        """
        Hook method called after writing data.

        This method can be overridden in subclasses to implement custom behavior
        when data is written to the file.

        :param __s: The bytes that were written
        :type __s: bytes
        """
        pass

    def writelines(self, __lines):
        """
        Write a list of lines to the file.

        :param __lines: List of byte strings to write
        :type __lines: list[bytes]
        :raises ValueError: If the file is closed
        """
        if self._closed:
            raise ValueError("I/O operation on closed file.")
        for line in __lines:
            self.write(line)

    def __next__(self):
        """
        Return the next line from the file.

        :raises ValueError: If the file is closed
        :raises UnsupportedOperation: Always, as this operation is not supported
        """
        if self._closed:
            raise ValueError("I/O operation on closed file.")
        raise UnsupportedOperation("__next__")

    def __iter__(self):
        """
        Return self as an iterator.

        :return: Self
        :rtype: BinaryProxyIO
        :raises ValueError: If the file is closed
        """
        if self._closed:
            raise ValueError("I/O operation on closed file.")
        return self

    def __exit__(self, __t, __value, __traceback):
        """
        Exit the runtime context related to this object.

        :param __t: Exception type
        :param __value: Exception value
        :param __traceback: Exception traceback
        """
        self.close()

"""
The decompressors of the methods of zip, behind one small push interface: ``feed(chunk) -> bytes`` and ``finish() -> bytes``.

The standard library covers stored, deflate, bzip2, lzma and xz (and zstd from Python 3.14); deflate64 needs ``inflate64``,
zstd before 3.14 needs ``zstandard`` (both are optional, see ``requirements-zip.txt``); the legacy methods are ports in
:mod:`hfutils.index.zip.legacy`. PPMd, JPEG and WavPack are recognized and refused with their method number.

The module contains:

* :data:`METHOD_NAMES`, :func:`method_name` - the names of the methods
* :func:`make_decompressor` - the decompressor of a method

Example::

    >>> import zlib
    >>> from hfutils.index.zip.codecs import make_decompressor
    >>> packer = zlib.compressobj(9, zlib.DEFLATED, -15)
    >>> packed = packer.compress(b'hello hello hello') + packer.flush()
    >>> decompressor = make_decompressor(8, 0, 17)
    >>> decompressor.feed(packed) + decompressor.finish()
    b'hello hello hello'
"""
import bz2
import lzma
import struct
import zlib
from typing import Optional

from .errors import ZipFormatError, ZipUnsupportedError
from .legacy import unshrink, expand, explode

METHOD_NAMES = {0: 'stored', 1: 'shrink', 2: 'reduce-1', 3: 'reduce-2', 4: 'reduce-3', 5: 'reduce-4', 6: 'implode', 8: 'deflate',
                9: 'deflate64', 12: 'bzip2', 14: 'lzma', 93: 'zstd', 95: 'xz', 96: 'jpeg', 97: 'wavpack', 98: 'ppmd'}


def method_name(method: int) -> str:
    """
    The name of a compression method.

    :param method: The method number of a zip record.
    :type method: int
    :return: The name, or ``'method N'`` for a number that has none.
    :rtype: str

    Example::

        >>> from hfutils.index.zip.codecs import method_name
        >>> method_name(8), method_name(95), method_name(1234)
        ('deflate', 'xz', 'method 1234')
    """
    return METHOD_NAMES.get(method, f'method {method}')


class _Stored:
    def feed(self, chunk: bytes) -> bytes:
        return chunk

    def finish(self) -> bytes:
        return b''


class _Object:
    """A decompressor object of the standard library or of an optional package."""

    def __init__(self, obj, name: str):
        self.obj, self.name = obj, name

    def feed(self, chunk: bytes) -> bytes:
        try:
            return self.obj.decompress(chunk)
        except Exception as err:  # zlib, bz2, lzma and the optional packages raise each their own types
            raise ZipFormatError(f'The {self.name} data is damaged: {err}') from err

    def finish(self) -> bytes:
        flush = getattr(self.obj, 'flush', None)
        if flush is None:
            return b''
        try:
            return flush() or b''
        except Exception as err:
            raise ZipFormatError(f'The {self.name} data is damaged: {err}') from err


class _Inflate64:
    """``inflate64`` names its method ``inflate``, the others ``decompress``."""

    def __init__(self, inflater):
        self.inflater = inflater

    def decompress(self, chunk: bytes) -> bytes:
        return self.inflater.inflate(chunk)


class _Lzma:
    """Zip's LZMA (method 14): a 4-byte header, the 5 property bytes, then a raw LZMA1 stream (ended by a marker or by the size)."""

    def __init__(self, flags: int, size: int):
        self.buf = b''
        self.obj = None
        self.size = size
        self.out = 0

    def feed(self, chunk: bytes) -> bytes:
        if self.obj is None:
            self.buf += chunk
            if len(self.buf) < 4:
                return b''
            props_size = struct.unpack_from('<H', self.buf, 2)[0]
            if props_size != 5:
                raise ZipFormatError(f'The lzma properties are {props_size} bytes, 5 expected.')
            if len(self.buf) < 4 + props_size:
                return b''
            props = self.buf[4]
            dict_size = struct.unpack_from('<I', self.buf, 5)[0]
            if props >= 9 * 5 * 5:
                raise ZipFormatError('The lzma properties are invalid.')
            lc, rest = props % 9, props // 9
            self.obj = lzma.LZMADecompressor(lzma.FORMAT_RAW, filters=[{
                'id': lzma.FILTER_LZMA1, 'lc': lc, 'lp': rest % 5, 'pb': rest // 5, 'dict_size': max(dict_size, 4096)}])
            chunk, self.buf = self.buf[4 + props_size:], b''
        if self.obj.eof:
            return b''
        try:
            out = self.obj.decompress(chunk)
        except lzma.LZMAError as err:
            raise ZipFormatError(f'The lzma data is damaged: {err}') from err
        if self.size is not None and self.out + len(out) > self.size:
            out = out[:self.size - self.out]
        self.out += len(out)
        return out

    def finish(self) -> bytes:
        return b''


class _Whole:
    """The legacy methods decode a whole member at once."""

    def __init__(self, method: int, flags: int, size: int):
        self.method, self.flags, self.size = method, flags, size
        self.parts = []

    def feed(self, chunk: bytes) -> bytes:
        self.parts.append(chunk)
        return b''

    def finish(self) -> bytes:
        data = b''.join(self.parts)
        if self.method == 1:
            return unshrink(data, self.size)
        if 2 <= self.method <= 5:
            return expand(data, self.size, self.method - 1)
        large, literal = bool(self.flags & 2), bool(self.flags & 4)
        try:
            return explode(data, self.size, large, literal)
        except ZipFormatError:
            return explode(data, self.size, large, literal, True)


def _zstd():
    try:
        from compression import zstd  # Python 3.14
        return lambda: zstd.ZstdDecompressor()
    except ImportError:
        pass
    try:
        import zstandard
        return lambda: zstandard.ZstdDecompressor().decompressobj()
    except ImportError:
        raise ZipUnsupportedError('A zstd member needs Python 3.14 or the `zstandard` package.', method=93) from None


def make_decompressor(method: int, flags: int, size: Optional[int]):
    """
    A decompressor for a member.

    :param method: The method number of the member (for AES, the one behind the encryption).
    :type method: int
    :param flags: The general purpose flags of the record (they carry the options of implode).
    :type flags: int
    :param size: The uncompressed size of the member (needed by LZMA without an end marker, and by the legacy methods).
    :type size: Optional[int]
    :return: An object with ``feed(chunk) -> bytes`` and ``finish() -> bytes``.
    :rtype: object
    :raises hfutils.index.zip.errors.ZipUnsupportedError: If the method cannot be decoded: PPMd, JPEG, WavPack, an unknown number,
        or a method whose optional package is not installed.

    Example::

        >>> from hfutils.index.zip.codecs import make_decompressor
        >>> decompressor = make_decompressor(0, 0, 5)
        >>> decompressor.feed(b'hello') + decompressor.finish()
        b'hello'
        >>> try:
        ...     make_decompressor(98, 0, 5)
        ... except Exception as err:
        ...     print(type(err).__name__, err.method)
        ZipUnsupportedError 98
    """
    if method == 0:
        return _Stored()
    if method == 8:
        return _Object(zlib.decompressobj(-15), 'deflate')
    if method == 9:
        try:
            import inflate64
        except ImportError:
            raise ZipUnsupportedError('A deflate64 member needs the `inflate64` package.', method=9) from None
        return _Object(_Inflate64(inflate64.Inflater()), 'deflate64')
    if method == 12:
        return _Object(bz2.BZ2Decompressor(), 'bzip2')
    if method == 14:
        return _Lzma(flags, size)
    if method == 93:
        return _Object(_zstd()(), 'zstd')
    if method == 95:
        return _Object(lzma.LZMADecompressor(lzma.FORMAT_XZ), 'xz')
    if 1 <= method <= 6:
        return _Whole(method, flags, size or 0)
    raise ZipUnsupportedError(f'The compression method {method} ({method_name(method)}) is not supported.', method=method)

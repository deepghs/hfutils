"""
The legacy compression methods of zip (Shrink, Reduce 1-4, Implode), which nothing in the standard library handles.

This is a Python port of the decompressors of hwzip 2.4 by Hans Wennborg (https://www.hanshq.net/zip.html, public domain), through
their JavaScript port in zip.js (BSD-3-Clause) that cheesecave-web vendors. They work on a whole member in memory: the methods
are rare and old, their archives are small. Damaged data raises :class:`hfutils.index.zip.errors.ZipFormatError`, never anything else.

The module contains:

* :func:`unshrink` - method 1
* :func:`expand` - methods 2-5
* :func:`explode` - method 6

Example::

    >>> import zlib
    >>> from hfutils.index.zip.directory import open_zip
    >>> from hfutils.index.zip.reader import ZipArchive
    >>> from hfutils.index.zip.source import FileSource
    >>> from hfutils.index.zip.legacy import unshrink
    >>> archive = ZipArchive(open_zip('legacy.zip', FileSource))
    >>> entry = archive.entry('FIRST.TXT')
    >>> data = unshrink(archive.stored_bytes('FIRST.TXT'), entry.size)
    >>> len(data), zlib.crc32(data) == entry.crc
    (1092, True)
"""
from typing import List, Optional, Tuple

from .errors import ZipFormatError


class _Bits:
    def __init__(self, data: bytes, what: str):
        self.data = bytes(data) + b'\x00\x00\x00'
        self.size = len(data) * 8
        self.pos = 0
        self.what = what

    def peek(self, count: int) -> int:
        i, off = self.pos >> 3, self.pos & 7
        value = self.data[i] | (self.data[i + 1] << 8) | (self.data[i + 2] << 16)
        return (value >> off) & ((1 << count) - 1)

    def read(self, count: int) -> int:
        if self.size - self.pos < count:
            raise ZipFormatError(f'Invalid {self.what} data: it ends early.')
        value = self.peek(count)
        self.pos += count
        return value

    def try_advance(self, count: int) -> bool:
        if self.size - self.pos < count:
            return False
        self.pos += count
        return True


# --- Shrink (method 1) -------------------------------------------------------------------------------------------------------

_MIN_CODE_SIZE, _MAX_CODE_SIZE = 9, 13
_MAX_CODE = (1 << _MAX_CODE_SIZE) - 1
_INVALID, _CONTROL, _UNKNOWN_LENGTH, _END = 0xffff, 256, 0xffff, -1


def unshrink(data: bytes, size: int) -> bytes:
    """
    Decode a member stored with the Shrink method (method 1): LZW with 9-13 bit codes and a partial-clear control code.

    :param data: The stored bytes of the member.
    :type data: bytes
    :param size: The uncompressed size of the member.
    :type size: int
    :return: The uncompressed bytes.
    :rtype: bytes
    :raises hfutils.index.zip.errors.ZipFormatError: If the data is damaged.

    Example::

        >>> import zlib
        >>> from hfutils.index.zip.directory import open_zip
        >>> from hfutils.index.zip.reader import ZipArchive
        >>> from hfutils.index.zip.source import FileSource
        >>> from hfutils.index.zip.legacy import unshrink
        >>> archive = ZipArchive(open_zip('legacy.zip', FileSource))
        >>> entry = archive.entry('FIRST.TXT')
        >>> data = unshrink(archive.stored_bytes('FIRST.TXT'), entry.size)
        >>> len(data), zlib.crc32(data) == entry.crc
        (1092, True)
    """
    bad = ZipFormatError('Invalid shrunk data.')
    reader = _Bits(data, 'shrunk')
    prefix = [_INVALID] * (_MAX_CODE + 1)
    ext = [0] * (_MAX_CODE + 1)
    lengths = [0] * (_MAX_CODE + 1)
    last = [0] * (_MAX_CODE + 1)
    for c in range(256):
        prefix[c], ext[c], lengths[c] = c, c, 1
    queue = list(range(_CONTROL + 1, _MAX_CODE + 1)) + [_INVALID]
    state = {'qi': 0, 'cs': _MIN_CODE_SIZE}
    out = bytearray(size + 1)  # one spare byte: a code may write its first byte before the size check

    def partial_clear():
        is_prefix = [False] * (_MAX_CODE + 1)
        for c in range(_CONTROL + 1, _MAX_CODE + 1):
            if prefix[c] != _INVALID:
                is_prefix[prefix[c]] = True
        n = 0
        for c in range(_CONTROL + 1, _MAX_CODE + 1):
            if not is_prefix[c]:
                prefix[c] = _INVALID
                queue[n] = c
                n += 1
        queue[n] = _INVALID
        state['qi'] = 0

    def read_code() -> int:
        while True:
            code = reader.peek(state['cs'])
            if not reader.try_advance(state['cs']):
                return _END
            if code != _CONTROL:
                return code
            control = reader.peek(state['cs'])
            if not reader.try_advance(state['cs']):
                return _INVALID
            if control == 1 and state['cs'] < _MAX_CODE_SIZE:
                state['cs'] += 1
            elif control == 2:
                partial_clear()
            else:
                return _INVALID

    pos = 0

    def output_code(code: int, prev: int, first: int) -> Tuple[int, int]:
        if code <= 0xff:
            out[pos] = code
            return code, 1
        if prefix[code] == _INVALID or prefix[code] == code:
            raise bad
        if lengths[code] != _UNKNOWN_LENGTH:
            n = lengths[code]
            if size - pos < n:
                raise bad
            src = last[code]
            for i in range(n):  # may overlap: byte by byte
                out[pos + i] = out[src + i]
            return out[pos], n
        # The length of this code is unknown because the code it builds on was freed by a partial clear right after it was sent
        # (hwzip's handling of what PKZIP writes). No archive here has such a stream and the encoder of the tests cannot make one
        # that this decoder accepts, so this branch is the one part of the port that no test runs.
        else:  # pragma: no cover
            pc = prefix[code]
            if pc == queue[state['qi']]:
                prefix[pc], ext[pc], lengths[pc], last[pc] = prev, first, lengths[prev] + 1, last[prev]
                out[pos] = first
            elif prefix[pc] == _INVALID:
                raise bad
            n = lengths[pc] + 1
            if size - pos < n:
                raise bad
            src = last[pc]
            for i in range(lengths[pc]):
                out[pos + i] = out[src + i]
            out[pos + n - 1] = ext[code]
            lengths[code], last[code] = n, pos
            return out[pos], n

    cur = read_code()
    if cur == _END:
        return b''
    if cur > 0xff or size == 0:
        raise bad
    first = cur
    out[pos] = cur
    last[cur] = pos
    pos += 1
    prev = cur
    while True:
        cur = read_code()
        if cur == _END:
            break
        if cur == _INVALID or pos == size:
            raise bad
        if cur == queue[state['qi']]:
            if prefix[prev] == _INVALID:
                raise bad
            prefix[cur], ext[cur], lengths[cur], last[cur] = prev, first, lengths[prev] + 1, last[prev]
            out[pos] = first
        first, n = output_code(cur, prev, first)
        new = queue[state['qi']]
        if new != _INVALID:
            state['qi'] += 1
            prefix[new], ext[new] = prev, first
            lengths[new] = _UNKNOWN_LENGTH if prefix[prev] == _INVALID else lengths[prev] + 1
            last[new] = last[prev]
        last[cur] = pos
        pos += n
        prev = cur
    return bytes(out[:pos])


# --- Reduce (methods 2-5) ----------------------------------------------------------------------------------------------------

_DLE = 144


def _follower_bits(n: int) -> int:
    return 5 if n > 16 else 4 if n > 8 else 3 if n > 4 else 2 if n > 2 else 1 if n > 0 else 0


def expand(data: bytes, size: int, factor: int) -> bytes:
    """
    Decode a member stored with the Reduce method (methods 2-5): a follower set per byte, plus (length, distance) runs.

    :param data: The stored bytes of the member.
    :type data: bytes
    :param size: The uncompressed size of the member.
    :type size: int
    :param factor: The compression factor: 1 to 4 (the method number minus 1).
    :type factor: int
    :return: The uncompressed bytes.
    :rtype: bytes
    :raises hfutils.index.zip.errors.ZipFormatError: If the data is damaged.

    Example::

        >>> import zlib
        >>> from hfutils.index.zip.directory import open_zip
        >>> from hfutils.index.zip.reader import ZipArchive
        >>> from hfutils.index.zip.source import FileSource
        >>> from hfutils.index.zip.legacy import expand
        >>> archive = ZipArchive(open_zip('reduce.zip', FileSource))
        >>> entry = archive.entry('first.txt')
        >>> data = expand(archive.stored_bytes('first.txt'), entry.size, entry.stored_method - 1)
        >>> len(data), zlib.crc32(data) == entry.crc
        (1092, True)
    """
    reader = _Bits(data, 'reduced')
    sets: List[Optional[Tuple[List[int], int]]] = [None] * 256
    for byte in range(255, -1, -1):
        n = reader.read(6)
        if n > 32:
            raise ZipFormatError('Invalid reduced data.')
        sets[byte] = ([reader.read(8) for _ in range(n)], _follower_bits(n))

    def next_byte(prev: int) -> int:
        followers, bits = sets[prev]
        if not followers:
            return reader.read(8)
        if reader.read(1):
            return reader.read(8)
        i = reader.read(bits)
        if i >= len(followers):
            raise ZipFormatError('Invalid reduced data.')
        return followers[i]

    length_bits = 8 - factor
    max_base = (1 << length_bits) - 1
    out = bytearray()
    cur = 0
    while len(out) < size:
        cur = next_byte(cur)
        if cur != _DLE:
            out.append(cur)
            continue
        cur = next_byte(cur)
        if cur == 0:
            out.append(_DLE)
            continue
        length_byte = cur
        length = length_byte & max_base
        if length == max_base:
            cur = next_byte(cur)
            length += cur
        length += 3
        cur = next_byte(cur)
        distance = (length_byte >> length_bits) * 256 + cur + 1
        if length > size - len(out):
            raise ZipFormatError('Invalid reduced data.')
        for _ in range(length):
            out.append(out[-distance] if distance <= len(out) else 0)
    return bytes(out)


# --- Implode (method 6) ------------------------------------------------------------------------------------------------------

_MAX_LEN = 16


class _Canonical:
    def __init__(self, lengths: List[int]):
        counts = [0] * (_MAX_LEN + 1)
        for n in lengths:
            counts[n] += 1
        counts[0] = 0
        codes = [0] * (_MAX_LEN + 1)
        index = [0] * (_MAX_LEN + 1)
        self.sentinel = [0] * (_MAX_LEN + 1)
        self.offset = [0] * (_MAX_LEN + 1)
        for n in range(1, _MAX_LEN + 1):
            codes[n] = (codes[n - 1] + counts[n - 1]) << 1
            self.sentinel[n] = (codes[n] + counts[n]) << (_MAX_LEN - n)
            index[n] = index[n - 1] + counts[n - 1]
            self.offset[n] = index[n] - codes[n]
        self.symbols = [0] * len(lengths)
        for symbol, n in enumerate(lengths):  # every symbol has a length: the tables are read in full before this is built
            self.symbols[index[n]] = symbol
            index[n] += 1

    def decode(self, reader: _Bits) -> int:
        raw = ~reader.peek(_MAX_LEN) & 0xffff
        bits = int(f'{raw:016b}'[::-1], 2)  # reverse16
        n = 1
        while bits >= self.sentinel[n]:  # the table is complete (checked when it was read), so the longest length always ends it
            n += 1
        reader.pos += n
        if reader.pos > reader.size:
            raise ZipFormatError('Invalid imploded data.')
        return self.symbols[(self.offset[n] + (bits >> (_MAX_LEN - n))) & 0xffff]


def _read_lengths(reader: _Bits, count: int) -> _Canonical:
    lengths = [0] * count
    counts = [0] * (_MAX_LEN + 1)
    index = 0
    for _ in range(reader.read(8) + 1):
        byte = reader.read(8)
        n, run = (byte & 0xf) + 1, (byte >> 4) + 1
        counts[n] += run
        if index + run > count:
            raise ZipFormatError('Invalid imploded data.')
        lengths[index:index + run] = [n] * run
        index += run
    if index < count:
        raise ZipFormatError('Invalid imploded data.')
    available = 1
    for n in range(1, _MAX_LEN + 1):
        available = available * 2 - counts[n]
        if available < 0:
            raise ZipFormatError('Invalid imploded data.')
    if available != 0:
        raise ZipFormatError('Invalid imploded data.')
    return _Canonical(lengths)


def explode(data: bytes, size: int, large_window: bool, literal_tree: bool, pk101_quirk: bool = False) -> bytes:
    """
    Decode a member stored with the Implode method (method 6): Shannon-Fano coded literals (optional), lengths and distances.

    ``pk101_quirk`` is the minimum match length PKZIP 1.01 wrote (the flag that selects the literal tree decided it, against the
    specification): the reader first decodes by the specification and, if that fails, with the quirk.

    :param data: The stored bytes of the member.
    :type data: bytes
    :param size: The uncompressed size of the member.
    :type size: int
    :param large_window: Whether the window is 8 KiB (flag bit 1) instead of 4 KiB.
    :type large_window: bool
    :param literal_tree: Whether literals are Shannon-Fano coded (flag bit 2).
    :type literal_tree: bool
    :param pk101_quirk: Whether to use the minimum length of PKZIP 1.01, defaults to ``False``.
    :type pk101_quirk: bool, optional
    :return: The uncompressed bytes.
    :rtype: bytes
    :raises hfutils.index.zip.errors.ZipFormatError: If the data is damaged.

    Example::

        >>> import zlib
        >>> from hfutils.index.zip.directory import open_zip
        >>> from hfutils.index.zip.reader import ZipArchive
        >>> from hfutils.index.zip.source import FileSource
        >>> from hfutils.index.zip.legacy import explode
        >>> archive = ZipArchive(open_zip('implode.zip', FileSource))
        >>> entry = archive.entry('first.txt')
        >>> data = explode(archive.stored_bytes('first.txt'), entry.size, bool(entry.flags & 2), bool(entry.flags & 4))
        >>> len(data), zlib.crc32(data) == entry.crc
        (1092, True)
    """
    reader = _Bits(data, 'imploded')
    literals = _read_lengths(reader, 256) if literal_tree else None
    lengths = _read_lengths(reader, 64)
    distances = _read_lengths(reader, 64)
    min_len = (3 if large_window else 2) if pk101_quirk else (3 if literal_tree else 2)
    distance_bits = 7 if large_window else 6
    out = bytearray()
    while len(out) < size:
        if reader.read(1):
            out.append(literals.decode(reader) if literals else reader.read(8))
            continue
        distance = reader.read(distance_bits)
        distance = (distance | (distances.decode(reader) << distance_bits)) + 1
        symbol = lengths.decode(reader)
        length = symbol + min_len
        if symbol == 63:
            length += reader.read(8)
        if length > size - len(out):
            raise ZipFormatError('Invalid imploded data.')
        for _ in range(length):
            out.append(out[-distance] if distance <= len(out) else 0)
    return bytes(out)

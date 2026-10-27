"""
Reading the directory of a zip: the end of central directory record (EOCD), the ZIP64 records, the central directory, volumes,
and telling a zip from what is not one.

The zip format is not tied to a file name, so nothing here looks at an extension to *refuse* a file: a valid EOCD is a zip (a
``.jar``, a ``.docx``, a self-extracting ``.exe`` or a file with no extension alike). Only when there is none, the first bytes
decide which error to give (a tar, a gzip, a Git LFS pointer, an error page, ...). Names with an extension matter for one thing:
finding the other volumes of a split archive (``X.zip.001``, ``X.z01``).

The module contains:

* :class:`ZipEntry`, :class:`ZipDirectory` - what a directory is made of
* :func:`build_directory` - read the directory of one file (the last volume)
* :func:`open_zip` - open an archive with every volume it needs
* :func:`find_eocd`, :func:`classify_non_zip`, :func:`not_a_zip`, :func:`raw_volume_name` - the pieces

Example::

    >>> from hfutils.index.zip.directory import build_directory
    >>> from hfutils.index.zip.source import FileSource
    >>> directory, source = build_directory(FileSource('archive.zip'))
    >>> sorted(directory.files)
    ['data/table.csv', 'docs/readme.md', 'hello.txt', 'images/noise.jpg']
    >>> directory.files['hello.txt'].size
    27
"""
import re
import struct
from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional, Tuple

from .crypto import parse_aes_extra
from .errors import (NotAZipError, ZipArchiveNotFound, ZipFormatError, ZipUnsupportedError, ZipVolumeError)
from .names import (guess_filename_encoding, unicode_path_extra, is_unicode_name, decode_name, member_path)
from .source import ZipSource, ConcatSource

_SIG_EOCD, _SIG_CD, _SIG_LOCAL = b'PK\x05\x06', b'PK\x01\x02', b'PK\x03\x04'
_SIG_Z64, _SIG_Z64_LOC, _SIG_SPAN = b'PK\x06\x06', b'PK\x06\x07', b'PK\x07\x08'
_TAIL = 22 + 65535 + 20 + 56 + 1024  # EOCD, its longest comment, the ZIP64 locator and record (+ slack)
_MAX_RAW_VOLUMES = 999


class _OffsetsBeforeStart(ZipFormatError):
    """The directory points before the first byte of the file: what is in front of it is somewhere else (a split volume)."""


@dataclass
class ZipEntry:
    """
    One record of the central directory.

    :param raw_name: The name as it is stored.
    :type raw_name: bytes
    :param name: The decoded name.
    :type name: str
    :param path: The normalized path, ``None`` for what is not a file (a directory).
    :type path: Optional[str]
    :param flags: The general purpose flags.
    :type flags: int
    :param method: The method the data is compressed with (for AES, the one behind the encryption).
    :type method: int
    :param stored_method: The method field of the record (99 for AES).
    :type stored_method: int
    :param csize: The size of the stored data.
    :type csize: int
    :param size: The uncompressed size.
    :type size: int
    :param crc: The CRC-32 of the uncompressed data.
    :type crc: int
    :param offset: The offset of the local header, in the one address space of all volumes.
    :type offset: int
    :param disk: The volume the member starts on.
    :type disk: int
    :param dos_time: The DOS modification time.
    :type dos_time: int
    :param dos_date: The DOS modification date.
    :type dos_date: int
    :param extra: The extra field data of the record.
    :type extra: bytes
    :param aes: ``(vendor version, key bits)`` of a WinZip AES member, defaults to ``None``.
    :type aes: Optional[Tuple[int, int]], optional
    :param is_dir: Whether the record is a directory, defaults to ``False``.
    :type is_dir: bool, optional

    Example::

        >>> from hfutils.index.zip.directory import build_directory
        >>> from hfutils.index.zip.source import FileSource
        >>> directory, source = build_directory(FileSource('archive.zip'))
        >>> entry = directory.files['hello.txt']
        >>> entry.size, entry.csize, entry.method, entry.encrypted
        (27, 61, 12, False)
    """
    raw_name: bytes
    name: str
    path: Optional[str]  # ``None`` for what is not a file
    flags: int
    method: int  # the method the data is compressed with (for AES, the one behind it)
    stored_method: int  # the method field of the record (99 for AES)
    csize: int
    size: int
    crc: int
    offset: int  # of the local header, in the one address space of all volumes
    disk: int
    dos_time: int
    dos_date: int
    extra: bytes
    aes: Optional[Tuple[int, int]] = None  # (vendor version, key bits)
    is_dir: bool = False

    @property
    def encrypted(self) -> bool:
        """
        Whether the member is encrypted: flag bit 0, or bit 6 (strong encryption sets both, but a writer may set only the latter).

        :return: ``True`` when the member is encrypted.
        :rtype: bool
        """
        return bool(self.flags & 0x41)  # bit 0, or bit 6 (strong encryption sets both, but a writer may set only the latter)

    @property
    def strong(self) -> bool:
        """
        Whether the member uses PKWARE strong encryption (flag bit 6), which is not supported.

        :return: ``True`` for strong encryption.
        :rtype: bool
        """
        return bool(self.flags & 0x40)


@dataclass
class ZipDirectory:
    """
    The directory of an archive.

    :param entries: Every record, directories included, in the order of the directory.
    :type entries: List[ZipEntry]
    :param files: The files by path, in the order of the directory; of duplicate names the first counts.
    :type files: Dict[str, ZipEntry]
    :param encoding: The encoding the non-Unicode names were decoded with.
    :type encoding: str
    :param comment: The comment of the archive.
    :type comment: bytes
    :param source: The source every ``offset`` of the entries refers to (all volumes together).
    :type source: ZipSource
    :param volumes: The names of the volumes, in order (empty when the directory was built from a bare source), defaults to ``[]``.
    :type volumes: List[str], optional
    :param tail_start: Where the first read of the end of the file started.
    :type tail_start: int, optional
    :param notes: What was repaired (ZIP64 records that were missing, ...), defaults to ``[]``.
    :type notes: List[str], optional

    Example::

        >>> from hfutils.index.zip.directory import build_directory
        >>> from hfutils.index.zip.source import FileSource
        >>> directory, source = build_directory(FileSource('archive.zip'))
        >>> len(directory.entries), directory.encoding, directory.comment, directory.notes
        (4, 'utf-8', b'', [])
    """
    entries: List[ZipEntry]
    files: Dict[str, ZipEntry]  # by path, in the order of the directory, the first of the duplicates
    encoding: str
    comment: bytes
    source: ZipSource
    volumes: List[str] = field(default_factory=list)
    tail_start: int = 0
    notes: List[str] = field(default_factory=list)  # what was repaired, e.g. ZIP64 records that were missing


# --- not a zip ---------------------------------------------------------------------------------------------------------------

def classify_non_zip(head: bytes, size: int) -> Tuple[Optional[str], str]:
    """
    Say what a file is that has no end of central directory record, from its first bytes.

    :param head: The first bytes of the file (512 are enough: a tar has its magic at 257).
    :type head: bytes
    :param size: The size of the whole file.
    :type size: int
    :return: ``(what, description)``; ``what`` is ``'empty'``, ``'tar'``, ``'gzip'``, ``'bzip2'``, ``'xz'``, ``'zstd'``, ``'7z'``,
        ``'rar'``, ``'png'``, ``'jpeg'``, ``'gif'``, ``'pdf'``, ``'git-lfs-pointer'``, ``'html'``, ``'json'`` or ``'truncated-zip'``,
        and ``None`` when nothing is recognized.
    :rtype: Tuple[Optional[str], str]

    Example::

        >>> from hfutils.index.zip.directory import classify_non_zip
        >>> classify_non_zip(b'\\x1f\\x8b' + bytes(10), 12)
        ('gzip', 'the file is gzip data')
        >>> classify_non_zip(b'', 0)
        ('empty', 'the file is empty')
        >>> classify_non_zip(b'plain text', 10)[0] is None
        True
    """
    if size == 0:
        return 'empty', 'the file is empty'
    checks = [
        (head[257:262] == b'ustar', 'tar', 'a tar archive'),
        (head[:2] == b'\x1f\x8b', 'gzip', 'gzip data'),
        (head[:3] == b'BZh', 'bzip2', 'bzip2 data'),
        (head[:6] == b'\xfd7zXZ\x00', 'xz', 'xz data'),
        (head[:4] == b'\x28\xb5\x2f\xfd', 'zstd', 'zstd data'),
        (head[:6] == b"7z\xbc\xaf'\x1c", '7z', 'a 7z archive'),
        (head[:4] == b'Rar!', 'rar', 'a rar archive'),
        (head[:8] == b'\x89PNG\r\n\x1a\n', 'png', 'a PNG image'),
        (head[:3] == b'\xff\xd8\xff', 'jpeg', 'a JPEG image'),
        (head[:6] in (b'GIF87a', b'GIF89a'), 'gif', 'a GIF image'),
        (head[:5] == b'%PDF-', 'pdf', 'a PDF document'),
        (head.startswith(b'version https://git-lfs.github.com/spec/'), 'git-lfs-pointer',
         'a Git LFS pointer, not the file itself'),
    ]
    for ok, what, text in checks:
        if ok:
            return what, f'the file is {text}'
    stripped = head.lstrip(b'\xef\xbb\xbf \t\r\n')[:64].lower()
    if stripped.startswith((b'<!doctype html', b'<html', b'<?xml')):
        return 'html', 'the file is an HTML or XML page (an error page instead of the archive?)'
    if stripped.startswith((b'{', b'[')) and size < 1 << 16:
        return 'json', 'the file is JSON text (an API error instead of the archive?)'
    if head[:4] in (_SIG_LOCAL, _SIG_SPAN):
        return 'truncated-zip', ('the file starts like a zip, but its end is missing: it is truncated, or it is one volume of a '
                                 'split archive (open the last volume)')
    return None, 'no zip end-of-directory record was found'


def not_a_zip(source: ZipSource) -> NotAZipError:
    """
    Build the error for a source that has no end record, from what its first bytes look like.

    :param source: The source that is not a zip.
    :type source: ZipSource
    :return: The error, to be raised by the caller.
    :rtype: hfutils.index.zip.errors.NotAZipError

    Example::

        >>> from hfutils.index.zip.directory import not_a_zip
        >>> from hfutils.index.zip.source import BytesSource
        >>> not_a_zip(BytesSource(b'<!DOCTYPE html><html></html>')).detected
        'html'
    """
    head = source.fetch_range(0, 512)
    what, text = classify_non_zip(head, source.size)
    return NotAZipError(f'{source.name} is not a zip archive: {text}.', detected=what)


# --- EOCD --------------------------------------------------------------------------------------------------------------------

def find_eocd(tail: bytes) -> Optional[int]:
    """
    Find the end of central directory record in the end of a file.

    The last signature whose comment length fits is taken, preferring one that ends exactly at the end of the data.

    :param tail: The last bytes of the file (at least 22, up to 64 KiB plus the record).
    :type tail: bytes
    :return: The position of the record in ``tail``, or ``None``.
    :rtype: Optional[int]

    Example::

        >>> from hfutils.index.zip.directory import find_eocd
        >>> with open('archive.zip', 'rb') as f:
        ...     data = f.read()
        >>> find_eocd(data) == len(data) - 22
        True
        >>> find_eocd(b'not a zip') is None
        True
    """
    pos = len(tail)
    fallback = None
    while True:
        pos = tail.rfind(_SIG_EOCD, 0, pos)
        if pos < 0:
            return fallback
        if pos + 22 <= len(tail):
            comment = struct.unpack_from('<H', tail, pos + 20)[0]
            if pos + 22 + comment == len(tail):
                return pos
            if pos + 22 + comment < len(tail) and fallback is None:
                fallback = pos  # a few bytes after the comment (padding)
        pos += 3


def _entry_from_record(buf: bytes, pos: int) -> Tuple[Optional[dict], int]:
    if buf[pos:pos + 4] != _SIG_CD or pos + 46 > len(buf):
        return None, pos
    (_made, _need, flags, method, dtime, ddate, crc, csize, size, nlen, elen, clen, disk, _iattr, _eattr,
     lho) = struct.unpack_from('<HHHHHHIIIHHHHHII', buf, pos + 4)
    end = pos + 46 + nlen + elen + clen
    if end > len(buf):
        return None, pos
    raw = buf[pos + 46:pos + 46 + nlen]
    extra = buf[pos + 46 + nlen:pos + 46 + nlen + elen]
    # ZIP64 extra field: exactly the fields whose 32-bit value is saturated, in this order
    i = 0
    while i + 4 <= len(extra):
        tag, n = struct.unpack_from('<HH', extra, i)
        if tag == 0x0001:
            body, j = extra[i + 4:i + 4 + n], 0
            if size == 0xffffffff and j + 8 <= len(body):
                size, j = struct.unpack_from('<Q', body, j)[0], j + 8
            if csize == 0xffffffff and j + 8 <= len(body):
                csize, j = struct.unpack_from('<Q', body, j)[0], j + 8
            if lho == 0xffffffff and j + 8 <= len(body):
                lho, j = struct.unpack_from('<Q', body, j)[0], j + 8
            if disk == 0xffff and j + 4 <= len(body):
                disk = struct.unpack_from('<I', body, j)[0]
        i += 4 + n
    return dict(raw=raw, extra=extra, flags=flags, method=method, dtime=dtime, ddate=ddate, crc=crc, csize=csize, size=size,
                disk=disk, lho=lho), end


def _read_cd_entries(cd: bytes) -> List[dict]:
    out, pos = [], 0
    while True:
        rec, nxt = _entry_from_record(cd, pos)
        if rec is None:
            return out
        out.append(rec)
        pos = nxt


def build_directory(source: ZipSource, *, encoding: Optional[str] = None, lang: str = 'en',
                    volumes: Optional[List[str]] = None,
                    load_previous: Optional[Callable[[int], List[ZipSource]]] = None) -> Tuple[ZipDirectory, ZipSource]:
    """
    Read the directory from the file that holds the end record (the last volume).

    The directory is found in front of the ZIP64 records, or of the end record; data in front of the archive (a self-extractor) is
    accounted for; ZIP64 records that an Info-ZIP written to a pipe never wrote are repaired (``notes`` says so). An Info-ZIP disk set is
    recognized by the end record saying it sits on disk ``n``: ``load_previous(n)`` then gives the volumes that come before.

    :param source: The source of the file that holds the end record.
    :type source: ZipSource
    :param encoding: The encoding of the names that are not Unicode, defaults to ``None`` (guessed).
    :type encoding: str, optional
    :param lang: A hint for guessing that encoding, defaults to ``'en'``.
    :type lang: str, optional
    :param volumes: The names of the volumes, kept in the result, defaults to ``None``.
    :type volumes: List[str], optional
    :param load_previous: Returns the ``n`` volumes before the last one, defaults to ``None``.
    :type load_previous: Callable[[int], List[ZipSource]], optional
    :return: The directory, and the source its offsets refer to (the one given, or all volumes together).
    :rtype: Tuple[ZipDirectory, ZipSource]
    :raises hfutils.index.zip.errors.NotAZipError: If there is no end record.
    :raises hfutils.index.zip.errors.ZipFormatError: If the directory is damaged or truncated.
    :raises hfutils.index.zip.errors.ZipUnsupportedError: If the directory is encrypted.
    :raises hfutils.index.zip.errors.ZipVolumeError: If the number of volumes is not the one the end record says.

    Example::

        >>> from hfutils.index.zip.directory import build_directory
        >>> from hfutils.index.zip.source import FileSource
        >>> directory, source = build_directory(FileSource('archive.zip'))
        >>> sorted(directory.files)[:2], source.size > 0
        (['data/table.csv', 'docs/readme.md'], True)
    """
    size = source.size
    if size == 0:
        raise not_a_zip(source)
    tail_start = max(0, size - _TAIL)
    tail = source.fetch(tail_start, size - tail_start)
    pos = find_eocd(tail)
    if pos is None:
        raise not_a_zip(source)
    eocd_at = tail_start + pos
    this_disk, cd_disk, _here, total, cd_size, cd_offset, comment_len = struct.unpack_from('<HHHHIIH', tail, pos + 4)
    comment = tail[pos + 22:pos + 22 + comment_len]
    notes: List[str] = []
    z64_at: Optional[int] = None
    z64_extensible = False

    def at(abs_pos: int, length: int) -> bytes:
        if abs_pos >= tail_start and abs_pos + length <= size:
            return tail[abs_pos - tail_start:abs_pos - tail_start + length]
        return source.fetch_range(abs_pos, length)

    saturated = (this_disk == 0xffff or cd_disk == 0xffff or total == 0xffff or cd_size == 0xffffffff or cd_offset == 0xffffffff)
    locator_at: Optional[int] = None
    if eocd_at >= 20 and at(eocd_at - 20, 4) == _SIG_Z64_LOC:
        locator_at = eocd_at - 20
        z_disk, z_off, _disks = struct.unpack_from('<IQI', at(eocd_at - 20, 20), 4)
        # In a disk set the record is in the last disk at an offset relative to that disk; in one file it is absolute.
        z64_at = z_off if z_disk >= 0 else None
        rec = at(z64_at, 56) if z64_at is not None and z64_at + 56 <= size else b''
        if rec[:4] == _SIG_Z64 and len(rec) >= 56:
            rec_size = struct.unpack_from('<Q', rec, 4)[0]
            z64_extensible = rec_size > 44
            _vm, _vn, this_disk, cd_disk, _h, total, cd_size, cd_offset = struct.unpack_from('<HHIIQQQQ', rec, 12)
        else:
            z64_at = None
            notes.append('the ZIP64 locator points to nothing')
    # Where the directory ends: in front of the ZIP64 record, else of the locator whose record is gone, else of the end record.
    end_of_cd = z64_at if z64_at is not None else (locator_at if locator_at is not None else eocd_at)
    if z64_at is None and cd_offset == 0xffffffff:
        # Info-ZIP written to a pipe (-fz): it keeps the 0xFFFFFFFF markers but the ZIP64 records never made it. The directory is
        # right in front of the EOCD, and its size is a plain 32-bit value.
        cd_offset = end_of_cd - cd_size
        notes.append('the ZIP64 records are missing; the directory was found in front of the end record')
    elif z64_at is None and saturated and cd_size == 0xffffffff:
        raise ZipFormatError(f'{source.name}: the end record says ZIP64 but its records are missing.')

    # Where the directory is: the offset is relative to the disk (or file) that holds it. A file with data in front of the
    # archive (a self-extractor) keeps the offsets it had, so the shift is the difference to where the directory really is.
    multi = this_disk > 0
    if multi:
        cd_pos = cd_offset
        if cd_pos + cd_size > size:
            cd_pos = end_of_cd - cd_size
    else:
        cd_pos = end_of_cd - cd_size
    shift = 0 if multi else cd_pos - cd_offset
    if cd_pos < 0:
        raise ZipFormatError(f'{source.name}: the central directory is larger than the file: it is truncated.')
    if shift < 0:
        raise _OffsetsBeforeStart(f'{source.name}: the directory points to data before the start of the file: the beginning of the '
                                  f'archive is missing (the last volume of a split archive?).')

    cd = at(cd_pos, cd_size)
    if cd_size and cd[:4] != _SIG_CD:
        if z64_extensible:
            raise ZipUnsupportedError('The central directory of this archive is encrypted; it cannot be listed.')
        raise ZipFormatError(f'{source.name}: no central directory where the end record says (damaged, or not a zip).')

    # volumes
    addr: ZipSource = source
    bases: List[int] = [0]
    if multi:
        previous = load_previous(this_disk) if load_previous else []
        parts = list(previous) + [source]
        if len(parts) != this_disk + 1:
            raise ZipVolumeError(f'{source.name}: the archive has {this_disk + 1} volumes, {len(parts)} found.')
        addr = ConcatSource(parts)
        bases = addr.bases

    raw_entries = _read_cd_entries(cd)
    unicode_flags = []
    for e in raw_entries:
        uni = unicode_path_extra(e['extra'], e['raw'])
        unicode_flags.append(uni)
    legacy = [e['raw'] for e, uni in zip(raw_entries, unicode_flags) if not is_unicode_name(e['flags'], uni)]
    chosen = encoding or guess_filename_encoding(legacy, lang)

    entries: List[ZipEntry] = []
    files: Dict[str, ZipEntry] = {}
    for e, uni in zip(raw_entries, unicode_flags):
        name = decode_name(e['raw'], e['flags'], uni, chosen)
        method, aes = e['method'], None
        if method == 99:
            info = parse_aes_extra(e['extra'])
            if info is None:
                raise ZipFormatError(f'{name}: an AES member without the AES extra field.')
            aes, method = (info[0], info[1]), info[2]
        disk = e['disk']
        if multi and disk >= len(bases):
            raise ZipFormatError(f'{name}: starts on disk {disk}, but the archive has {len(bases)} volumes.')
        offset = (bases[disk] if multi else 0) + e['lho'] + shift
        path = member_path(name)
        is_dir = path is None or name.endswith('/')
        entry = ZipEntry(raw_name=e['raw'], name=name, path=None if is_dir else path, flags=e['flags'], method=method,
                         stored_method=e['method'], csize=e['csize'], size=e['size'], crc=e['crc'], offset=offset, disk=disk,
                         dos_time=e['dtime'], dos_date=e['ddate'], extra=e['extra'], aes=aes, is_dir=is_dir)
        entries.append(entry)
        if entry.path is not None and entry.path not in files:
            files[entry.path] = entry
    directory = ZipDirectory(entries=entries, files=files, encoding=chosen, comment=comment, source=addr,
                             volumes=list(volumes or []), tail_start=tail_start, notes=notes)
    return directory, addr


# --- volumes -----------------------------------------------------------------------------------------------------------------

_RAW_VOLUME = re.compile(r'^(?P<base>.*)\.(?P<n>\d{3})$')
_DISK_VOLUME = re.compile(r'^(?P<base>.*)\.z(?P<n>\d{2,})$', re.I)


def raw_volume_name(base: str, n: int) -> str:
    """
    The name of a volume of a 7-Zip style split archive.

    :param base: The name without the volume number (``'x.zip'`` for ``'x.zip.001'``).
    :type base: str
    :param n: The number of the volume, from 1.
    :type n: int
    :return: The name of the volume.
    :rtype: str

    Example::

        >>> from hfutils.index.zip.directory import raw_volume_name
        >>> raw_volume_name('x.zip', 3)
        'x.zip.003'
    """
    return f'{base}.{n:03d}'


def open_zip(name: str, open_named: Callable[[str], Optional[ZipSource]], *, encoding: Optional[str] = None,
             lang: str = 'en') -> ZipDirectory:
    """
    Open the archive ``name`` with every volume it needs.

    Any volume of a split archive opens the whole set: ``X.zip.001`` ... (a byte split of one zip), or ``X.z01`` ... ``X.zip`` (an
    Info-ZIP disk set). A file named like a volume that is a whole zip by itself is opened as that (``a.000``). The extension is never a
    reason to refuse a file.

    :param name: The path of the archive, or of one volume of it.
    :type name: str
    :param open_named: Returns the source of a path, or ``None`` when it does not exist.
    :type open_named: Callable[[str], Optional[ZipSource]]
    :param encoding: The encoding of the names that are not Unicode, defaults to ``None`` (guessed).
    :type encoding: str, optional
    :param lang: A hint for guessing that encoding, defaults to ``'en'``.
    :type lang: str, optional
    :return: The directory; its ``volumes`` are the names of all the volumes, in order.
    :rtype: ZipDirectory
    :raises hfutils.index.zip.errors.ZipArchiveNotFound: If ``name`` does not exist.
    :raises hfutils.index.zip.errors.ZipVolumeError: If a volume of a split archive is missing.
    :raises hfutils.index.zip.errors.NotAZipError: If it is not a zip.

    Example::

        >>> import os
        >>> from hfutils.index.zip.directory import open_zip
        >>> from hfutils.index.zip.source import FileSource
        >>> directory = open_zip('split.zip.002', lambda path: FileSource(path) if os.path.exists(path) else None)
        >>> directory.volumes
        ['split.zip.001', 'split.zip.002', 'split.zip.003']
    """
    requested = open_named(name)
    if requested is None:
        raise ZipArchiveNotFound(f'{name}: no such archive.')
    raw = _RAW_VOLUME.match(name)
    disk = _DISK_VOLUME.match(name)
    if raw:
        base = raw.group('base')
        try:  # a file named like a volume that is a whole zip by itself is one (``a.000``, ``a.001``)
            return build_directory(requested, encoding=encoding, lang=lang, volumes=[name])[0]
        except (NotAZipError, _OffsetsBeforeStart):
            pass
        first = open_named(raw_volume_name(base, 1))
        if first is None:
            raise ZipVolumeError(f'Missing split volume {raw_volume_name(base, 1)}: the zip directory is in the last volume '
                                 f'and every volume is needed.', missing=[raw_volume_name(base, 1)])
        parts, n = [first], 2
        while n <= _MAX_RAW_VOLUMES:
            nxt = open_named(raw_volume_name(base, n))
            if nxt is None:
                break
            parts.append(nxt)
            n += 1
        gap = n
        later = [k for k in range(gap + 1, gap + 9) if open_named(raw_volume_name(base, k)) is not None] if n <= _MAX_RAW_VOLUMES \
            else []
        source = ConcatSource(parts)
        try:
            if later:
                raise NotAZipError('gap')
            directory, _addr = build_directory(source, encoding=encoding, lang=lang,
                                               volumes=[raw_volume_name(base, k + 1) for k in range(len(parts))])
            return directory
        except NotAZipError as err:
            if later or err.detected in (None, 'truncated-zip'):
                missing = raw_volume_name(base, gap)
                raise ZipVolumeError(f'Missing split volume {missing}: the zip directory is in the last volume.',
                                     missing=[missing]) from None
            raise
    if disk:
        base = disk.group('base')
        for ext in ('.zip', '.ZIP', '.Zip'):
            source = open_named(base + ext)
            if source is not None:
                name = base + ext
                break
        else:
            raise ZipVolumeError(f'Missing split volume {base}.zip: the zip directory is in the last volume.',
                                 missing=[base + '.zip'])
    else:
        source = requested

    stem = name.rsplit('.', 1)[0] if '.' in name.rsplit('/', 1)[-1] else name

    def load_previous(count: int) -> List[ZipSource]:
        parts = []
        for k in range(1, count + 1):
            vol_name = f'{stem}.z{k:02d}'
            vol = open_named(vol_name)
            if vol is None:
                raise ZipVolumeError(f'Missing split volume {vol_name}: this archive is made of {count + 1} volumes and every '
                                     f'one is needed.', missing=[vol_name])
            parts.append(vol)
        return parts

    directory, _addr = build_directory(source, encoding=encoding, lang=lang, load_previous=load_previous,
                                       volumes=[name])
    if isinstance(_addr, ConcatSource) and len(_addr.parts) > 1:
        directory.volumes = [f'{stem}.z{k:02d}' for k in range(1, len(_addr.parts))] + [name]
    return directory

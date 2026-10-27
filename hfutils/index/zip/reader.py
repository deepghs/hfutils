"""
Reading the members of a zip: fetch the compressed bytes with Range-sized windows, decrypt, decompress, check the CRC.

The password policy follows cheesecave-web: the passwords that worked are remembered by the archive object and tried first,
:meth:`ZipArchive.unlock` checks a password against the few smallest encrypted members (a member over 8 MiB is checked by its
password verifier only), members that are not encrypted can always be read, and errors tell the four cases apart
(``fetch`` / ``format`` / ``password`` / ``unsupported``, see :mod:`hfutils.index.zip.errors`).

The module contains:

* :class:`ZipArchive` - a directory plus the methods to read members
* :data:`PasswordTyping` - what the ``password`` arguments accept: a ``str``, ``bytes``, or an iterable of them

Example::

    >>> from hfutils.index.zip.directory import open_zip
    >>> from hfutils.index.zip.reader import ZipArchive
    >>> from hfutils.index.zip.source import FileSource
    >>> archive = ZipArchive(open_zip('locked.zip', FileSource))
    >>> archive.read('hello.txt', password='secret')
    b'hello from the zip fixture\\n'
"""
import struct
import zlib
from typing import Iterable, Iterator, List, Optional, Union

from .codecs import make_decompressor
from .crypto import AesDecryptor, ZipCryptoDecryptor, aes_verifier_matches, zipcrypto_check_byte
from .directory import ZipDirectory, ZipEntry
from .errors import ZipFormatError, ZipPasswordError, ZipPasswordRequiredError, ZipUnsupportedError

PasswordTyping = Union[str, bytes, Iterable[Union[str, bytes]], None]
_SAMPLE = 8  # how many of the smallest encrypted members unlock() looks at
_FULL_CHECK_LIMIT = 8 << 20


def _no_password_fits(e: ZipEntry, last: Optional[Exception]) -> ZipPasswordError:
    """ZipCrypto's check is one byte: when a password passed it and the CRC refused the member, say that it may be damaged."""
    if last is not None and 'CRC' in str(last):
        return ZipPasswordError(f'{e.name}: wrong password (or the data is damaged: the CRC does not match).')
    return ZipPasswordError(f'{e.name}: wrong password.')


def _passwords(value: PasswordTyping) -> List[bytes]:
    if value is None:
        return []
    if isinstance(value, (str, bytes)):
        value = [value]
    return [v.encode('utf-8') if isinstance(v, str) else bytes(v) for v in value]


class ZipArchive:
    """
    An opened zip: its directory and the methods to read members.

    Cheap to keep: the state is the directory and the passwords that worked. The directory is shared and never changes; the passwords
    belong to this object (the public functions make a new one for every call, so no password outlives it).

    :param directory: The directory, see :func:`hfutils.index.zip.directory.open_zip`.
    :type directory: ZipDirectory
    :param password: Passwords to try, defaults to ``None``.
    :type password: Union[str, bytes, Iterable[Union[str, bytes]]], optional

    :ivar directory: The directory.
    :vartype directory: ZipDirectory
    :ivar passwords: The passwords that worked or were given, the most recent first.
    :vartype passwords: List[bytes]

    Example::

        >>> from hfutils.index.zip.directory import open_zip
        >>> from hfutils.index.zip.reader import ZipArchive
        >>> from hfutils.index.zip.source import FileSource
        >>> archive = ZipArchive(open_zip('archive.zip', FileSource))
        >>> archive.paths()
        ['hello.txt', 'data/table.csv', 'docs/readme.md', 'images/noise.jpg']
        >>> 'hello.txt' in archive, archive.encrypted
        (True, False)
    """

    def __init__(self, directory: ZipDirectory, password: PasswordTyping = None):
        """
        Build the archive object.

        :param directory: The directory.
        :type directory: ZipDirectory
        :param password: Passwords to try, defaults to ``None``.
        :type password: Union[str, bytes, Iterable[Union[str, bytes]]], optional
        :return: ``None``.
        :rtype: None
        """
        self.directory = directory
        self.passwords: List[bytes] = _passwords(password)

    # --- listing ------------------------------------------------------------------------------------------------------------

    @property
    def source(self):
        """
        The source every offset of the entries refers to.

        :return: The source of all the volumes.
        :rtype: ZipSource
        """
        return self.directory.source

    def stored_bytes(self, path: str) -> bytes:
        """
        The bytes of a member as they are stored: encrypted and compressed, nothing decoded.

        :param path: The path of the member.
        :type path: str
        :return: The stored bytes (``csize`` of them).
        :rtype: bytes
        :raises FileNotFoundError: If there is no such member.
        :raises hfutils.index.zip.errors.ZipFormatError: If the local header is not where the directory says.

        Example::

            >>> from hfutils.index.zip.directory import open_zip
            >>> from hfutils.index.zip.reader import ZipArchive
            >>> from hfutils.index.zip.source import FileSource
            >>> archive = ZipArchive(open_zip('archive.zip', FileSource))
            >>> entry = archive.entry('hello.txt')
            >>> len(archive.stored_bytes('hello.txt')) == entry.csize
            True
        """
        return b''.join(self._chunks(self.entry(path)))

    def paths(self) -> List[str]:
        """
        The paths of the files in the archive, in the order of the directory.

        :return: The paths (directories are left out, names are normalized, of duplicates the first counts).
        :rtype: List[str]

        Example::

            >>> from hfutils.index.zip.directory import open_zip
            >>> from hfutils.index.zip.reader import ZipArchive
            >>> from hfutils.index.zip.source import FileSource
            >>> archive = ZipArchive(open_zip('archive.zip', FileSource))
            >>> archive.paths()
            ['hello.txt', 'data/table.csv', 'docs/readme.md', 'images/noise.jpg']
        """
        return list(self.directory.files)

    def entry(self, path: str) -> ZipEntry:
        """
        The record of a file.

        :param path: The path of the member.
        :type path: str
        :return: The record.
        :rtype: ZipEntry
        :raises FileNotFoundError: If there is no such member.

        Example::

            >>> from hfutils.index.zip.directory import open_zip
            >>> from hfutils.index.zip.reader import ZipArchive
            >>> from hfutils.index.zip.source import FileSource
            >>> archive = ZipArchive(open_zip('archive.zip', FileSource))
            >>> archive.entry('hello.txt').size
            27
            >>> try:
            ...     archive.entry('nope.txt')
            ... except FileNotFoundError as err:
            ...     print(err)
            File 'nope.txt' not found in the zip archive.
        """
        try:
            return self.directory.files[path]
        except KeyError:
            raise FileNotFoundError(f'File {path!r} not found in the zip archive.') from None

    def __contains__(self, path: str) -> bool:
        """
        Whether a path is a file of the archive.

        :param path: The path of the member.
        :type path: str
        :return: ``True`` when it is.
        :rtype: bool

        Example::

            >>> from hfutils.index.zip.directory import open_zip
            >>> from hfutils.index.zip.reader import ZipArchive
            >>> from hfutils.index.zip.source import FileSource
            >>> archive = ZipArchive(open_zip('archive.zip', FileSource))
            >>> 'hello.txt' in archive, 'docs' in archive
            (True, False)
        """
        return path in self.directory.files

    @property
    def encrypted(self) -> bool:
        """
        Whether any member is encrypted.

        :return: ``True`` when at least one is.
        :rtype: bool
        """
        return any(e.encrypted for e in self.directory.files.values())

    # --- passwords ----------------------------------------------------------------------------------------------------------

    def _candidates(self, extra: PasswordTyping = None) -> List[bytes]:
        out: List[bytes] = []
        for pw in _passwords(extra) + self.passwords:
            if pw not in out:
                out.append(pw)
        return out

    def _remember(self, pw: bytes) -> None:
        if pw in self.passwords:
            self.passwords.remove(pw)
        self.passwords.insert(0, pw)

    def unlock(self, password: Union[str, bytes]) -> bool:
        """
        Check a password against the smallest encrypted members and remember it if it fits.

        At most 8 members are tried, the smallest ones; a member over 8 MiB is checked by its password verifier or check byte only, the
        others by reading them (so the CRC confirms the password).

        :param password: The password.
        :type password: Union[str, bytes]
        :return: ``True`` when the password opens them, or when nothing is encrypted (there is nothing to refuse).
        :rtype: bool

        Example::

            >>> from hfutils.index.zip.directory import open_zip
            >>> from hfutils.index.zip.reader import ZipArchive
            >>> from hfutils.index.zip.source import FileSource
            >>> archive = ZipArchive(open_zip('locked.zip', FileSource))
            >>> archive.unlock('wrong'), archive.passwords
            (False, [])
            >>> archive.unlock('secret'), archive.passwords
            (True, [b'secret'])
        """
        pw = _passwords(password)[0]
        sample = sorted((e for e in self.directory.files.values() if e.encrypted and not e.strong),
                        key=lambda e: e.csize)[:_SAMPLE]
        if not sample:
            return True
        for e in sample:
            if not self._check(e, pw):
                return False
        self._remember(pw)
        return True

    def _check(self, e: ZipEntry, pw: bytes) -> bool:
        """Does ``pw`` open ``e``? The whole member for a small one, the verifier for a big one."""
        try:
            if e.aes is not None:
                head = self._raw(e, 0, min(e.csize, 24))
                return aes_verifier_matches(pw, e.aes[1], head)
            if e.size <= _FULL_CHECK_LIMIT:
                self._read(e, None, pw)
                return True
            header = self._raw(e, 0, 12)
            return ZipCryptoDecryptor.header_matches(pw, header, self._check_byte(e))
        except ZipPasswordError:
            return False
        except ZipFormatError:
            return False

    # --- reading ------------------------------------------------------------------------------------------------------------

    def _data_start(self, e: ZipEntry) -> int:
        head_len = 30 + len(e.raw_name) + len(e.extra) + 32
        head = self.source.fetch_range(e.offset, head_len)
        if len(head) < 30 or head[:4] != b'PK\x03\x04':
            raise ZipFormatError(f'{e.name}: no local header at offset {e.offset}: the archive is damaged, or a volume is wrong.')
        nlen, elen = struct.unpack_from('<HH', head, 26)
        return e.offset + 30 + nlen + elen

    def _raw(self, e: ZipEntry, start: int, length: int) -> bytes:
        return self.source.fetch_range(self._data_start(e) + start, length)

    def _check_byte(self, e: ZipEntry) -> int:
        return zipcrypto_check_byte(e.crc, e.dos_time, bool(e.flags & 8))

    def _chunks(self, e: ZipEntry, limit: Optional[int] = None) -> Iterator[bytes]:
        """The stored bytes of a member, in windows; small members come in the one request that also brings the local header
        (with a ``limit`` only a first piece does, so that reading the head of a big member does not fetch all of it)."""
        src = self.source
        first = 30 + len(e.raw_name) + len(e.extra) + 32
        if e.csize <= (256 << 10 if limit is None else 64 << 10):
            first += e.csize
        elif limit is not None:
            first += 64 << 10
        head = src.fetch_range(e.offset, min(first, src.window))
        if len(head) < 30 or head[:4] != b'PK\x03\x04':
            raise ZipFormatError(f'{e.name}: no local header at offset {e.offset}: the archive is damaged, or a volume is wrong.')
        nlen, elen = struct.unpack_from('<HH', head, 26)
        start = 30 + nlen + elen
        have = head[start:start + e.csize]
        if have:
            yield have
        pos = e.offset + start + len(have)
        end = e.offset + start + e.csize
        if pos < end and len(have) < min(e.csize, len(head) - start):
            raise ZipFormatError(f'{e.name}: inconsistent local header.')  # pragma: no cover
        while pos < end:
            chunk = src.fetch_range(pos, min(src.window, end - pos))
            if not chunk:
                raise ZipFormatError(f'{e.name}: the archive ends in the middle of the member (truncated).')
            yield chunk
            pos += len(chunk)

    def _stream(self, e: ZipEntry, limit: Optional[int], password: Optional[bytes]) -> Iterator[bytes]:
        """The plain bytes of a member as they are decoded. The checks that need the whole member (size, CRC, the AES tag) raise at
        the end of the iteration; a partial read (``limit``) stops fetching as soon as it has enough and checks nothing."""
        decomp = make_decompressor(e.method, e.flags, e.size)  # an unsupported method is reported even without a password
        if not e.encrypted:
            dec = None
        elif e.aes is not None:
            dec = AesDecryptor(password, e.aes[1])
        else:
            dec = ZipCryptoDecryptor(password, self._check_byte(e))
        got = crc = 0
        for chunk in self._chunks(e, limit):
            plain = dec.feed(chunk) if dec else chunk
            data = decomp.feed(plain) if plain else b''
            if limit is not None and got + len(data) >= limit:
                data = data[:limit - got]
                if data:
                    yield data
                return
            if data:
                got += len(data)
                crc = zlib.crc32(data, crc)
                yield data
        tail = b''
        if dec:
            tail = dec.finish()
            tail = decomp.feed(tail) if tail else b''
        tail += decomp.finish()
        if tail:
            got += len(tail)
            crc = zlib.crc32(tail, crc)
            if limit is not None and got > limit:
                tail = tail[:len(tail) - (got - limit)]
                yield tail
                return
            yield tail
        ambiguous = e.encrypted and e.aes is None  # ZipCrypto: a wrong password that passed the one-byte check
        bad = ZipPasswordError if ambiguous else ZipFormatError
        hint = ' (a wrong password, or the data is damaged)' if ambiguous else ' (the data is damaged)'
        if got != e.size:
            raise bad(f'{e.name}: {got} bytes came out, {e.size} expected{hint}.')
        if not (e.aes is not None and e.aes[0] == 2) and (crc & 0xffffffff) != e.crc:
            raise bad(f'{e.name}: the CRC does not match{hint}.')

    def _read(self, e: ZipEntry, limit: Optional[int], password: Optional[bytes]) -> bytes:
        return b''.join(self._stream(e, limit, password))

    def _with_password(self, e: ZipEntry, limit: Optional[int], password: PasswordTyping) -> Iterator[bytes]:
        """Stream a member with the first password that opens it. A ZipCrypto false accept only shows at the end of the member:
        ``read`` then goes on with the next password, a streaming caller gets the error."""
        if not e.encrypted:
            yield from self._stream(e, limit, None)
            return
        if e.strong:
            raise ZipUnsupportedError(f'{e.name}: PKWARE strong encryption is not supported.', method=e.stored_method)
        make_decompressor(e.method, e.flags, e.size)
        candidates = self._candidates(password)
        if not candidates:
            raise ZipPasswordRequiredError(f'{e.name} is encrypted: a password is needed.')
        last: Optional[Exception] = None
        for pw in candidates:
            gen = self._stream(e, limit, pw)
            try:
                first = next(gen)
            except StopIteration:
                self._remember(pw)
                return
            except ZipPasswordError as err:
                last = err
                continue
            self._remember(pw)
            yield first
            yield from gen
            return
        raise _no_password_fits(e, last)

    def iter_chunks(self, path: str, limit: Optional[int] = None, password: PasswordTyping = None) -> Iterator[bytes]:
        """
        The content of a member in chunks, for members that do not fit in memory.

        The first of the passwords that opens the member is used (``password`` first, then the remembered ones). A ZipCrypto false accept
        shows only at the end of the member, as a :class:`hfutils.index.zip.errors.ZipPasswordError` raised by the last step of the
        iteration; :meth:`read` goes on with the next password instead.

        :param path: The path of the member.
        :type path: str
        :param limit: Stop after this many bytes (nothing after them is fetched, and no CRC is checked), defaults to ``None``.
        :type limit: int, optional
        :param password: Passwords to try first, defaults to ``None``.
        :type password: Union[str, bytes, Iterable[Union[str, bytes]]], optional
        :return: The chunks.
        :rtype: Iterator[bytes]
        :raises FileNotFoundError: If there is no such member.
        :raises hfutils.index.zip.errors.ZipPasswordRequiredError: If the member is encrypted and there is no password.
        :raises hfutils.index.zip.errors.ZipPasswordError: If no password opens it.
        :raises hfutils.index.zip.errors.ZipUnsupportedError: If the method or the encryption is not supported.
        :raises hfutils.index.zip.errors.ZipFormatError: If the data is damaged.

        Example::

            >>> from hfutils.index.zip.directory import open_zip
            >>> from hfutils.index.zip.reader import ZipArchive
            >>> from hfutils.index.zip.source import FileSource
            >>> archive = ZipArchive(open_zip('locked.zip', FileSource))
            >>> b''.join(archive.iter_chunks('hello.txt', password='secret'))
            b'hello from the zip fixture\\n'
        """
        return self._with_password(self.entry(path), limit, password)

    def read(self, path: str, limit: Optional[int] = None, password: PasswordTyping = None) -> bytes:
        """
        The content of a member.

        Encrypted members are tried with ``password`` and then with the remembered passwords; when a wrong password passes ZipCrypto's
        one-byte check and fails the CRC, the next one is tried. A password that works is remembered.

        :param path: The path of the member.
        :type path: str
        :param limit: Return only the first bytes: only the windows that hold them are fetched, and the CRC cannot be checked, defaults to
            ``None``.
        :type limit: int, optional
        :param password: Passwords to try first, defaults to ``None``.
        :type password: Union[str, bytes, Iterable[Union[str, bytes]]], optional
        :return: The content.
        :rtype: bytes
        :raises FileNotFoundError: If there is no such member.
        :raises hfutils.index.zip.errors.ZipPasswordRequiredError: If the member is encrypted and there is no password.
        :raises hfutils.index.zip.errors.ZipPasswordError: If no password opens it.
        :raises hfutils.index.zip.errors.ZipUnsupportedError: If the method or the encryption is not supported.
        :raises hfutils.index.zip.errors.ZipFormatError: If the data is damaged (size or CRC do not match, a local header is missing).

        Example::

            >>> from hfutils.index.zip.directory import open_zip
            >>> from hfutils.index.zip.reader import ZipArchive
            >>> from hfutils.index.zip.source import FileSource
            >>> archive = ZipArchive(open_zip('archive.zip', FileSource))
            >>> archive.read('hello.txt')
            b'hello from the zip fixture\\n'
            >>> archive.read('hello.txt', limit=5)
            b'hello'
        """
        e = self.entry(path)
        if not e.encrypted:
            return self._read(e, limit, None)
        if e.strong:
            raise ZipUnsupportedError(f'{e.name}: PKWARE strong encryption is not supported.', method=e.stored_method)
        make_decompressor(e.method, e.flags, e.size)
        candidates = self._candidates(password)
        if not candidates:
            raise ZipPasswordRequiredError(f'{e.name} is encrypted: a password is needed.')
        last: Optional[Exception] = None
        for pw in candidates:
            try:
                data = self._read(e, limit, pw)
            except ZipPasswordError as err:
                last = err
                continue
            self._remember(pw)
            return data
        raise _no_password_fits(e, last)

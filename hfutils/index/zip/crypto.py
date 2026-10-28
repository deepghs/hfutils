"""
The two encryptions of zip that can be read without a native library of their own: traditional PKWARE encryption ("ZipCrypto") and
WinZip AES (method 99). PKWARE strong encryption (flag bit 6) is refused by the reader.

Both are push filters like the decompressors: ``feed(chunk) -> bytes`` returns the decrypted bytes of what has been given so far
(the AES one holds back the trailing 10-byte authentication code and checks it in ``finish``).

ZipCrypto's password check is one byte, so one wrong password in 256 passes it: a bad CRC after a ZipCrypto member is therefore
reported as "password or damaged". The WinZip AES check is two bytes plus an HMAC over the whole member. AES needs the optional
``cryptography`` package (``pip install hfutils[zip]``); checking a password against the verifier does not.

The module contains:

* :class:`ZipCryptoKeys`, :class:`ZipCryptoDecryptor`, :func:`zipcrypto_check_byte` - traditional encryption
* :func:`parse_aes_extra`, :func:`aes_derive`, :func:`aes_verifier_matches`, :class:`AesDecryptor` - WinZip AES

Example::

    >>> from hfutils.index.zip.directory import open_zip
    >>> from hfutils.index.zip.reader import ZipArchive
    >>> from hfutils.index.zip.source import FileSource
    >>> archive = ZipArchive(open_zip('locked.zip', FileSource))
    >>> entry = archive.entry('hello.txt')
    >>> stored = archive.stored_bytes('hello.txt')
    >>> from hfutils.index.zip.crypto import ZipCryptoDecryptor, zipcrypto_check_byte
    >>> check = zipcrypto_check_byte(entry.crc, entry.dos_time, bool(entry.flags & 8))
    >>> decryptor = ZipCryptoDecryptor(b'secret', check)
    >>> decryptor.feed(stored) + decryptor.finish()
    b'hello from the zip fixture\\n'
"""
import hashlib
import hmac
import struct
from typing import Optional, Tuple

from .errors import ZipFormatError, ZipPasswordError, ZipUnsupportedError

_CRC_TABLE = [0] * 256
for _i in range(256):
    _c = _i
    for _ in range(8):
        _c = (_c >> 1) ^ 0xedb88320 if _c & 1 else _c >> 1
    _CRC_TABLE[_i] = _c


class ZipCryptoKeys:
    """
    The three 32-bit keys of the traditional cipher, derived from a password.

    :param password: The password.
    :type password: bytes

    :ivar k0: First key.
    :vartype k0: int
    :ivar k1: Second key.
    :vartype k1: int
    :ivar k2: Third key.
    :vartype k2: int

    Example::

        >>> from hfutils.index.zip.crypto import ZipCryptoKeys
        >>> keys = ZipCryptoKeys(b'secret')
        >>> keys.k0 != ZipCryptoKeys(b'other').k0
        True
    """

    def __init__(self, password: bytes):
        """
        Derive the keys.

        :param password: The password.
        :type password: bytes
        :return: ``None``.
        :rtype: None
        """
        self.k0, self.k1, self.k2 = 0x12345678, 0x23456789, 0x34567890
        for b in password:
            self.update(b)

    def update(self, b: int) -> None:
        """
        Advance the keys with one plain byte.

        :param b: A plain byte.
        :type b: int
        :return: ``None``.
        :rtype: None

        Example::

            >>> from hfutils.index.zip.crypto import ZipCryptoKeys
            >>> keys = ZipCryptoKeys(b'')
            >>> before = keys.k0
            >>> keys.update(65)
            >>> keys.k0 != before
            True
        """
        self.k0 = _CRC_TABLE[(self.k0 ^ b) & 0xff] ^ (self.k0 >> 8)
        self.k1 = ((self.k1 + (self.k0 & 0xff)) * 134775813 + 1) & 0xffffffff
        self.k2 = _CRC_TABLE[(self.k2 ^ (self.k1 >> 24)) & 0xff] ^ (self.k2 >> 8)

    def decrypt(self, data: bytes) -> bytes:
        """
        Decrypt bytes, advancing the keys with every plain byte.

        :param data: Encrypted bytes.
        :type data: bytes
        :return: The plain bytes.
        :rtype: bytes

        Example::

            >>> from hfutils.index.zip.crypto import ZipCryptoKeys
            >>> ZipCryptoKeys(b'secret').decrypt(b'')
            b''
        """
        out = bytearray(len(data))
        k0, k1, k2 = self.k0, self.k1, self.k2
        table = _CRC_TABLE
        for i, c in enumerate(data):
            t = (k2 | 2) & 0xffff
            c ^= ((t * (t ^ 1)) >> 8) & 0xff
            out[i] = c
            k0 = table[(k0 ^ c) & 0xff] ^ (k0 >> 8)
            k1 = ((k1 + (k0 & 0xff)) * 134775813 + 1) & 0xffffffff
            k2 = table[(k2 ^ (k1 >> 24)) & 0xff] ^ (k2 >> 8)
        self.k0, self.k1, self.k2 = k0, k1, k2
        return bytes(out)


def zipcrypto_check_byte(crc: int, mtime_dos: int, has_descriptor: bool) -> int:
    """
    The byte the 12-byte header of a ZipCrypto member must end with.

    It is the high byte of the CRC, or of the modification time when the member has a data descriptor (the CRC is not known yet when
    the header is written).

    :param crc: The CRC-32 of the member.
    :type crc: int
    :param mtime_dos: The DOS modification time of the record.
    :type mtime_dos: int
    :param has_descriptor: Whether the member has a data descriptor (flag bit 3).
    :type has_descriptor: bool
    :return: The check byte.
    :rtype: int

    Example::

        >>> from hfutils.index.zip.crypto import zipcrypto_check_byte
        >>> zipcrypto_check_byte(0x12345678, 0xabcd, False), zipcrypto_check_byte(0x12345678, 0xabcd, True)
        (18, 171)
    """
    return ((mtime_dos & 0xffff) >> 8) if has_descriptor else (crc >> 24) & 0xff


class ZipCryptoDecryptor:
    """
    Decrypts a ZipCrypto member; the first 12 bytes are the header, whose last byte is the password check.

    :param password: The password.
    :type password: bytes
    :param check: The byte the header must end with, see :func:`zipcrypto_check_byte`.
    :type check: int
    :param verify: Whether to refuse a password whose check byte is wrong, defaults to ``True``.
    :type verify: bool, optional

    Example::

        >>> from hfutils.index.zip.directory import open_zip
        >>> from hfutils.index.zip.reader import ZipArchive
        >>> from hfutils.index.zip.source import FileSource
        >>> archive = ZipArchive(open_zip('locked.zip', FileSource))
        >>> entry = archive.entry('hello.txt')
        >>> stored = archive.stored_bytes('hello.txt')
        >>> from hfutils.index.zip.crypto import ZipCryptoDecryptor, zipcrypto_check_byte
        >>> check = zipcrypto_check_byte(entry.crc, entry.dos_time, bool(entry.flags & 8))
        >>> decryptor = ZipCryptoDecryptor(b'secret', check)
        >>> b''.join(decryptor.feed(stored[i:i + 5]) for i in range(0, len(stored), 5))
        b'hello from the zip fixture\\n'
    """

    def __init__(self, password: bytes, check: int, *, verify: bool = True):
        """
        Build the decryptor.

        :param password: The password.
        :type password: bytes
        :param check: The byte the header must end with.
        :type check: int
        :param verify: Whether to refuse a password whose check byte is wrong, defaults to ``True``.
        :type verify: bool, optional
        :return: ``None``.
        :rtype: None
        """
        self.keys = ZipCryptoKeys(password)
        self.check = check
        self.verify = verify
        self.header = b''

    def feed(self, chunk: bytes) -> bytes:
        """
        Decrypt the next bytes of the member.

        :param chunk: The next stored bytes (the header comes first and may be split over chunks).
        :type chunk: bytes
        :return: The plain bytes of this chunk (nothing while the header is incomplete).
        :rtype: bytes
        :raises hfutils.index.zip.errors.ZipPasswordError: If the check byte of the header is not the expected one.

        Example::

            >>> from hfutils.index.zip.directory import open_zip
            >>> from hfutils.index.zip.reader import ZipArchive
            >>> from hfutils.index.zip.source import FileSource
            >>> archive = ZipArchive(open_zip('locked.zip', FileSource))
            >>> entry = archive.entry('hello.txt')
            >>> stored = archive.stored_bytes('hello.txt')
            >>> from hfutils.index.zip.crypto import ZipCryptoDecryptor, zipcrypto_check_byte
            >>> check = zipcrypto_check_byte(entry.crc, entry.dos_time, bool(entry.flags & 8))
            >>> ZipCryptoDecryptor(b'secret', check).feed(stored[:5])
            b''
            >>> ZipCryptoDecryptor(b'secret', check).feed(stored)
            b'hello from the zip fixture\\n'
        """
        if len(self.header) < 12:
            take = 12 - len(self.header)
            self.header += chunk[:take]
            chunk = chunk[take:]
            if len(self.header) < 12:
                return b''
            plain = self.keys.decrypt(self.header)
            if self.verify and plain[11] != self.check:
                raise ZipPasswordError('Wrong password.')
        return self.keys.decrypt(chunk) if chunk else b''

    def finish(self) -> bytes:
        """
        End the member.

        :return: Nothing is held back: always ``b''``.
        :rtype: bytes
        :raises hfutils.index.zip.errors.ZipFormatError: If the member was shorter than its 12-byte header.

        Example::

            >>> from hfutils.index.zip.crypto import ZipCryptoDecryptor
            >>> decryptor = ZipCryptoDecryptor(b'secret', 0)
            >>> decryptor.feed(b'12345')
            b''
            >>> try:
            ...     decryptor.finish()
            ... except Exception as err:
            ...     print(type(err).__name__)
            ZipFormatError
        """
        if len(self.header) < 12:
            raise ZipFormatError('The encrypted member is shorter than its 12-byte header.')
        return b''

    @staticmethod
    def header_matches(password: bytes, header: bytes, check: int) -> bool:
        """
        Tell whether a password passes the check of a member, without decrypting it.

        :param password: The password.
        :type password: bytes
        :param header: The first 12 bytes of the member.
        :type header: bytes
        :param check: The byte the header must end with.
        :type check: int
        :return: ``True`` when the password passes (one wrong password in 256 does).
        :rtype: bool

        Example::

            >>> from hfutils.index.zip.directory import open_zip
            >>> from hfutils.index.zip.reader import ZipArchive
            >>> from hfutils.index.zip.source import FileSource
            >>> archive = ZipArchive(open_zip('locked.zip', FileSource))
            >>> entry = archive.entry('hello.txt')
            >>> stored = archive.stored_bytes('hello.txt')
            >>> from hfutils.index.zip.crypto import ZipCryptoDecryptor, zipcrypto_check_byte
            >>> check = zipcrypto_check_byte(entry.crc, entry.dos_time, bool(entry.flags & 8))
            >>> ZipCryptoDecryptor.header_matches(b'secret', stored[:12], check)
            True
        """
        return ZipCryptoKeys(password).decrypt(header)[11] == check


# --- WinZip AES --------------------------------------------------------------------------------------------------------------

AES_KEY_BITS = {1: 128, 2: 192, 3: 256}
_SALT_SIZE = {128: 8, 192: 12, 256: 16}


def parse_aes_extra(extra: bytes) -> Optional[Tuple[int, int, int]]:
    """
    Read the WinZip AES extra field (0x9901) of a record.

    :param extra: The extra field data of the record.
    :type extra: bytes
    :return: ``(vendor version, key bits, real compression method)``, or ``None`` when there is no such field.
    :rtype: Optional[Tuple[int, int, int]]
    :raises hfutils.index.zip.errors.ZipUnsupportedError: If the key strength is not one of the three the format defines.

    Example::

        >>> import struct
        >>> from hfutils.index.zip.crypto import parse_aes_extra
        >>> parse_aes_extra(struct.pack('<HHH2sBH', 0x9901, 7, 2, b'AE', 3, 8))
        (2, 256, 8)
        >>> parse_aes_extra(b'') is None
        True
    """
    pos = 0
    while pos + 4 <= len(extra):
        tag, size = struct.unpack_from('<HH', extra, pos)
        if tag == 0x9901 and size >= 7:
            version, _vendor, strength, method = struct.unpack_from('<H2sBH', extra, pos + 4)
            if strength not in AES_KEY_BITS:
                raise ZipUnsupportedError(f'The WinZip AES strength {strength} is unknown.', method=99)
            return version, AES_KEY_BITS[strength], method
        pos += 4 + size
    return None


def _cryptography():
    try:
        from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
        return Cipher, algorithms, modes
    except ImportError:
        raise ZipUnsupportedError('A WinZip AES member needs the `cryptography` package (pip install hfutils[zip]).',
                                  method=99) from None


def aes_derive(password: bytes, salt: bytes, bits: int) -> Tuple[bytes, bytes, bytes]:
    """
    Derive the keys of a WinZip AES member from the password and the salt of the member (PBKDF2-HMAC-SHA1, 1000 rounds).

    :param password: The password.
    :type password: bytes
    :param salt: The salt at the start of the member.
    :type salt: bytes
    :param bits: The key size: 128, 192 or 256.
    :type bits: int
    :return: ``(encryption key, authentication key, 2-byte password verifier)``.
    :rtype: Tuple[bytes, bytes, bytes]

    Example::

        >>> from hfutils.index.zip.crypto import aes_derive
        >>> key, auth, verifier = aes_derive(b'secret', bytes(16), 256)
        >>> len(key), len(auth), len(verifier)
        (32, 32, 2)
    """
    n = bits // 8
    derived = hashlib.pbkdf2_hmac('sha1', password, salt, 1000, 2 * n + 2)
    return derived[:n], derived[n:2 * n], derived[2 * n:]


def aes_verifier_matches(password: bytes, bits: int, head: bytes) -> bool:
    """
    Check a password against the salt and the 2-byte verifier at the start of an AES member, without decrypting it and without the
    ``cryptography`` package.

    :param password: The password.
    :type password: bytes
    :param bits: The key size: 128, 192 or 256.
    :type bits: int
    :param head: At least the first ``salt + 2`` bytes of the member.
    :type head: bytes
    :return: ``True`` when the verifier matches (one wrong password in 65536 does).
    :rtype: bool

    Example::

        >>> from hfutils.index.zip.directory import open_zip
        >>> from hfutils.index.zip.reader import ZipArchive
        >>> from hfutils.index.zip.source import FileSource
        >>> from hfutils.index.zip.crypto import aes_verifier_matches
        >>> archive = ZipArchive(open_zip('aes.zip', FileSource))
        >>> head = archive.stored_bytes('hello.txt')[:18]
        >>> aes_verifier_matches(b'secret', 256, head), aes_verifier_matches(b'wrong', 256, head)
        (True, False)
    """
    size = _SALT_SIZE[bits]
    return aes_derive(password, head[:size], bits)[2] == head[size:size + 2]


class AesDecryptor:
    """
    Decrypts a WinZip AES member: AES-CTR (the counter is little endian and starts at 1) with an HMAC-SHA1 tag of 10 bytes at its end.

    The salt and the verifier come first, the tag last; ``feed`` holds the last 10 bytes back until it knows there is more, and
    ``finish`` checks them.

    :param password: The password.
    :type password: bytes
    :param bits: The key size: 128, 192 or 256.
    :type bits: int
    :raises hfutils.index.zip.errors.ZipUnsupportedError: If the ``cryptography`` package is not installed.

    Example::

        >>> from hfutils.index.zip.directory import open_zip
        >>> from hfutils.index.zip.reader import ZipArchive
        >>> from hfutils.index.zip.source import FileSource
        >>> from hfutils.index.zip.crypto import AesDecryptor
        >>> archive = ZipArchive(open_zip('aes.zip', FileSource))
        >>> stored = archive.stored_bytes('hello.txt')
        >>> decryptor = AesDecryptor(b'secret', 256)
        >>> decryptor.feed(stored) + decryptor.finish()
        b'hello from the zip fixture\\n'
    """

    def __init__(self, password: bytes, bits: int):
        """
        Build the decryptor.

        :param password: The password.
        :type password: bytes
        :param bits: The key size: 128, 192 or 256.
        :type bits: int
        :return: ``None``.
        :rtype: None
        :raises hfutils.index.zip.errors.ZipUnsupportedError: If the ``cryptography`` package is not installed.
        """
        self.password, self.bits = password, bits
        self.salt_size = _SALT_SIZE[bits]
        self.head = b''
        self.tail = b''
        self.pending = b''
        self.mac = None
        self.ecb = None
        self.counter = 1
        self.Cipher = _cryptography()

    def _start(self) -> None:
        Cipher, algorithms, modes = self.Cipher
        key, auth, expected = aes_derive(self.password, self.head[:self.salt_size], self.bits)
        if self.head[self.salt_size:] != expected:
            raise ZipPasswordError('Wrong password.')
        self.mac = hmac.new(auth, digestmod=hashlib.sha1)
        self.ecb = Cipher(algorithms.AES(key), modes.ECB()).encryptor()

    def _xor(self, data: bytes) -> bytes:
        blocks = (len(data) + 15) // 16
        counters = b''.join(struct.pack('<Q', c) + b'\x00' * 8 for c in range(self.counter, self.counter + blocks))
        self.counter += blocks
        stream = self.ecb.update(counters)[:len(data)]
        return (int.from_bytes(data, 'little') ^ int.from_bytes(stream, 'little')).to_bytes(len(data), 'little')

    def feed(self, chunk: bytes) -> bytes:
        """
        Decrypt the next bytes of the member.

        :param chunk: The next stored bytes.
        :type chunk: bytes
        :return: The plain bytes that are complete (whole AES blocks; nothing while the salt and verifier are incomplete).
        :rtype: bytes
        :raises hfutils.index.zip.errors.ZipPasswordError: If the verifier does not match the password.

        Example::

            >>> from hfutils.index.zip.directory import open_zip
            >>> from hfutils.index.zip.reader import ZipArchive
            >>> from hfutils.index.zip.source import FileSource
            >>> from hfutils.index.zip.crypto import AesDecryptor
            >>> stored = ZipArchive(open_zip('aes.zip', FileSource)).stored_bytes('hello.txt')
            >>> AesDecryptor(b'secret', 256).feed(stored[:10])
            b''
        """
        need = self.salt_size + 2
        if self.mac is None:
            take = chunk[:need - len(self.head)]
            self.head += take
            chunk = chunk[len(take):]
            if len(self.head) < need:
                return b''
            self._start()
        data = self.tail + chunk
        body, self.tail = data[:-10], data[-10:]
        if not body:
            return b''
        self.mac.update(body)
        data = self.pending + body
        whole = len(data) // 16 * 16
        self.pending = data[whole:]
        return self._xor(data[:whole]) if whole else b''

    def finish(self) -> bytes:
        """
        End the member: decrypt what was held back and check the authentication code.

        :return: The last plain bytes.
        :rtype: bytes
        :raises hfutils.index.zip.errors.ZipFormatError: If the member is shorter than its header and tag, or the tag does not match.

        Example::

            >>> from hfutils.index.zip.crypto import AesDecryptor
            >>> try:
            ...     AesDecryptor(b'secret', 256).finish()
            ... except Exception as err:
            ...     print(type(err).__name__)
            ZipFormatError
        """
        if self.mac is None or len(self.tail) < 10:
            raise ZipFormatError('The AES encrypted member is shorter than its header and authentication code.')
        out = self._xor(self.pending) if self.pending else b''
        self.pending = b''
        if not hmac.compare_digest(self.mac.digest()[:10], self.tail):
            raise ZipFormatError('The authentication code of the AES member does not match: the data is damaged.')
        return out

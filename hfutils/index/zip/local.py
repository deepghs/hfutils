"""
Random access to the members of a zip on the local disk, the counterpart of :mod:`hfutils.index.local_fetch` for tar archives.

The zip's own central directory is the index: nothing is written next to the archive. Split archives open from any of their
volumes (``X.zip.001``, ``X.z01`` / ``X.zip``). The format is recognized by its content, never by the extension.

The ``password`` of the functions is a ``str``, ``bytes`` or a list of them. ``encoding`` forces the code page of names that are
not Unicode (``'shift_jis'``, ``'gbk'``, ...), ``lang`` is a hint for guessing it (``'ru'``, ``'ja'``). Every error is a
:class:`hfutils.index.zip.errors.ZipIndexError` with a ``kind``.

The module contains:

* :func:`zip_get_index`, :func:`zip_list_files`, :func:`zip_file_exists`, :func:`zip_file_info`, :func:`zip_file_size` - the directory
* :func:`zip_file_read`, :func:`zip_file_write_bytes`, :func:`zip_file_download` - the members
* :func:`zip_cache_reset` - forget the directories read so far

Example::

    >>> from hfutils.index import zip_list_files, zip_file_read
    >>> zip_list_files('archive.zip')
    ['hello.txt', 'data/table.csv', 'docs/readme.md', 'images/noise.jpg']
    >>> zip_file_read('archive.zip', 'hello.txt')
    b'hello from the zip fixture\\n'
"""
import os
from typing import BinaryIO, Dict, List, Optional, Tuple

from cachetools import LRUCache

from .api import entry_info, index_info, write_member, download_member
from .directory import open_zip
from .reader import ZipArchive, PasswordTyping
from .source import FileSource

_cache = LRUCache(maxsize=128)


def _stat_key(name: str):
    try:
        st = os.stat(name)
    except OSError:
        return None
    return st.st_mtime_ns, st.st_size


def _open(archive_file: str, password: PasswordTyping = None, encoding: Optional[str] = None, lang: str = 'en',
          no_cache: bool = False) -> ZipArchive:
    touched: Dict[str, Optional[Tuple[int, int]]] = {}

    def opener(name: str):
        if not os.path.isfile(name):
            touched[name] = None
            return None
        touched[name] = _stat_key(name)
        return FileSource(name)

    key = (os.path.abspath(archive_file), encoding, lang)
    cached = None if no_cache else _cache.get(key)
    if cached is not None:
        directory, stamps = cached
        if all(_stat_key(name) == stamp for name, stamp in stamps.items()):
            return ZipArchive(directory, password)
    directory = open_zip(archive_file, opener, encoding=encoding, lang=lang)
    if not no_cache:
        _cache[key] = (directory, dict(touched))
    return ZipArchive(directory, password)


def zip_get_index(archive_file: str, encoding: Optional[str] = None, lang: str = 'en', no_cache: bool = False) -> Dict:
    """
    Read the directory of the archive.

    The answer is ``{'files': {path: info}, 'encoding', 'volumes', 'comment', 'encrypted', 'notes', 'archive_size'}``. Each ``info`` has
    ``size``, ``compressed_size``, ``crc32``, ``method``, ``method_name``, ``encrypted``, ``offset`` and the ``volume`` the member starts
    on.

    :param archive_file: The path of the archive, or of one of its volumes.
    :type archive_file: str
    :param encoding: Encoding of the names that are not Unicode (``shift_jis``, ``gbk``, ``ibm866``, ...), defaults to ``None`` (guessed).
    :type encoding: str, optional
    :param lang: Hint for guessing that encoding (``'ru'``, ``'ja'``, ...), defaults to ``'en'``.
    :type lang: str, optional
    :param no_cache: Read the directory again even if it is cached, defaults to ``False``.
    :type no_cache: bool, optional
    :return: The directory.
    :rtype: Dict
    :raises hfutils.index.zip.errors.ZipArchiveNotFound: If the archive does not exist (a :class:`FileNotFoundError` too).
    :raises hfutils.index.zip.errors.NotAZipError: If it is not a zip (``err.detected`` says what it looks like).
    :raises hfutils.index.zip.errors.ZipVolumeError: If a volume of a split archive is missing.
    :raises hfutils.index.zip.errors.ZipUnsupportedError: If the directory is encrypted.

    Example::

        >>> from hfutils.index import zip_get_index
        >>> index = zip_get_index('archive.zip')
        >>> index['encoding'], index['encrypted'], index['files']['hello.txt']['size']
        ('utf-8', False, 27)
    """
    return index_info(_open(archive_file, None, encoding, lang, no_cache))


def zip_list_files(archive_file: str, encoding: Optional[str] = None, lang: str = 'en', no_cache: bool = False) -> List[str]:
    """
    List the files of the archive.

    Directories are left out, names are normalized (no empty segment, ``.`` or ``..``), and of duplicate names the first counts.

    :param archive_file: The path of the archive, or of one of its volumes.
    :type archive_file: str
    :param encoding: Encoding of the names that are not Unicode (``shift_jis``, ``gbk``, ``ibm866``, ...), defaults to ``None`` (guessed).
    :type encoding: str, optional
    :param lang: Hint for guessing that encoding (``'ru'``, ``'ja'``, ...), defaults to ``'en'``.
    :type lang: str, optional
    :param no_cache: Read the directory again even if it is cached, defaults to ``False``.
    :type no_cache: bool, optional
    :return: The paths, in the order of the directory.
    :rtype: List[str]
    :raises hfutils.index.zip.errors.ZipArchiveNotFound: If the archive does not exist (a :class:`FileNotFoundError` too).
    :raises hfutils.index.zip.errors.NotAZipError: If it is not a zip (``err.detected`` says what it looks like).
    :raises hfutils.index.zip.errors.ZipVolumeError: If a volume of a split archive is missing.

    Example::

        >>> from hfutils.index import zip_list_files
        >>> zip_list_files('archive.zip')
        ['hello.txt', 'data/table.csv', 'docs/readme.md', 'images/noise.jpg']
        >>> zip_list_files('split.zip.002')[:2]
        ['blob.bin', 'data/table.csv']
    """
    return _open(archive_file, None, encoding, lang, no_cache).paths()


def zip_file_exists(archive_file: str, file_in_archive: str, encoding: Optional[str] = None, lang: str = 'en') -> bool:
    """
    Tell whether the archive has a file of that path.

    :param archive_file: The path of the archive, or of one of its volumes.
    :type archive_file: str
    :param file_in_archive: The path of the member in the archive.
    :type file_in_archive: str
    :param encoding: Encoding of the names that are not Unicode (``shift_jis``, ``gbk``, ``ibm866``, ...), defaults to ``None`` (guessed).
    :type encoding: str, optional
    :param lang: Hint for guessing that encoding (``'ru'``, ``'ja'``, ...), defaults to ``'en'``.
    :type lang: str, optional
    :return: ``True`` when it has.
    :rtype: bool
    :raises hfutils.index.zip.errors.ZipArchiveNotFound: If the archive does not exist (a :class:`FileNotFoundError` too).
    :raises hfutils.index.zip.errors.NotAZipError: If it is not a zip (``err.detected`` says what it looks like).
    :raises hfutils.index.zip.errors.ZipVolumeError: If a volume of a split archive is missing.

    Example::

        >>> from hfutils.index import zip_file_exists
        >>> zip_file_exists('archive.zip', 'hello.txt'), zip_file_exists('archive.zip', 'docs'), zip_file_exists('archive.zip', 'x')
        (True, False, False)
    """
    return file_in_archive in _open(archive_file, None, encoding, lang)


def zip_file_info(archive_file: str, file_in_archive: str, encoding: Optional[str] = None, lang: str = 'en') -> Dict:
    """
    The record of a member, see :func:`zip_get_index` for its keys.

    :param archive_file: The path of the archive, or of one of its volumes.
    :type archive_file: str
    :param file_in_archive: The path of the member in the archive.
    :type file_in_archive: str
    :param encoding: Encoding of the names that are not Unicode (``shift_jis``, ``gbk``, ``ibm866``, ...), defaults to ``None`` (guessed).
    :type encoding: str, optional
    :param lang: Hint for guessing that encoding (``'ru'``, ``'ja'``, ...), defaults to ``'en'``.
    :type lang: str, optional
    :return: The information.
    :rtype: Dict
    :raises hfutils.index.zip.errors.ZipArchiveNotFound: If the archive does not exist (a :class:`FileNotFoundError` too).
    :raises hfutils.index.zip.errors.NotAZipError: If it is not a zip (``err.detected`` says what it looks like).
    :raises hfutils.index.zip.errors.ZipVolumeError: If a volume of a split archive is missing.
    :raises FileNotFoundError: If there is no such member.

    Example::

        >>> from hfutils.index import zip_file_info
        >>> info = zip_file_info('archive.zip', 'hello.txt')
        >>> info['size'], info['method_name'], info['encrypted']
        (27, 'bzip2', False)
    """
    return entry_info(_open(archive_file, None, encoding, lang), file_in_archive)


def zip_file_size(archive_file: str, file_in_archive: str, encoding: Optional[str] = None, lang: str = 'en') -> int:
    """
    The uncompressed size of a member.

    :param archive_file: The path of the archive, or of one of its volumes.
    :type archive_file: str
    :param file_in_archive: The path of the member in the archive.
    :type file_in_archive: str
    :param encoding: Encoding of the names that are not Unicode (``shift_jis``, ``gbk``, ``ibm866``, ...), defaults to ``None`` (guessed).
    :type encoding: str, optional
    :param lang: Hint for guessing that encoding (``'ru'``, ``'ja'``, ...), defaults to ``'en'``.
    :type lang: str, optional
    :return: The size in bytes.
    :rtype: int
    :raises hfutils.index.zip.errors.ZipArchiveNotFound: If the archive does not exist (a :class:`FileNotFoundError` too).
    :raises hfutils.index.zip.errors.NotAZipError: If it is not a zip (``err.detected`` says what it looks like).
    :raises hfutils.index.zip.errors.ZipVolumeError: If a volume of a split archive is missing.
    :raises FileNotFoundError: If there is no such member.

    Example::

        >>> from hfutils.index import zip_file_size
        >>> zip_file_size('archive.zip', 'hello.txt')
        27
    """
    return _open(archive_file, None, encoding, lang).entry(file_in_archive).size


def zip_file_read(archive_file: str, file_in_archive: str, password: PasswordTyping = None, limit: Optional[int] = None,
                  encoding: Optional[str] = None, lang: str = 'en') -> bytes:
    """
    The content of a member.

    :param archive_file: The path of the archive, or of one of its volumes.
    :type archive_file: str
    :param file_in_archive: The path of the member in the archive.
    :type file_in_archive: str
    :param password: Passwords to try (a ``str``, ``bytes`` or a list of them), defaults to ``None``.
    :type password: Union[str, bytes, Iterable[Union[str, bytes]]], optional
    :param limit: Return only the first bytes: only the part of the archive that holds them is fetched, and the CRC cannot be checked,
        defaults to ``None``.
    :type limit: int, optional
    :param encoding: Encoding of the names that are not Unicode (``shift_jis``, ``gbk``, ``ibm866``, ...), defaults to ``None`` (guessed).
    :type encoding: str, optional
    :param lang: Hint for guessing that encoding (``'ru'``, ``'ja'``, ...), defaults to ``'en'``.
    :type lang: str, optional
    :return: The content (its first ``limit`` bytes if given).
    :rtype: bytes
    :raises hfutils.index.zip.errors.ZipArchiveNotFound: If the archive does not exist (a :class:`FileNotFoundError` too).
    :raises hfutils.index.zip.errors.NotAZipError: If it is not a zip (``err.detected`` says what it looks like).
    :raises hfutils.index.zip.errors.ZipVolumeError: If a volume of a split archive is missing.
    :raises FileNotFoundError: If there is no such member.
    :raises hfutils.index.zip.errors.ZipPasswordRequiredError: If the member is encrypted and there is no password.
    :raises hfutils.index.zip.errors.ZipPasswordError: If no password opens it.
    :raises hfutils.index.zip.errors.ZipUnsupportedError: If the method or the encryption is not supported.
    :raises hfutils.index.zip.errors.ZipFormatError: If the data is damaged (size or CRC do not match).

    Example::

        >>> from hfutils.index import zip_file_read
        >>> zip_file_read('archive.zip', 'hello.txt')
        b'hello from the zip fixture\\n'
        >>> zip_file_read('archive.zip', 'hello.txt', limit=5)
        b'hello'
        >>> zip_file_read('locked.zip', 'hello.txt', password='secret')
        b'hello from the zip fixture\\n'
    """
    return _open(archive_file, password, encoding, lang).read(file_in_archive, limit=limit, password=password)


def zip_file_write_bytes(archive_file: str, file_in_archive: str, bin_file: BinaryIO, password: PasswordTyping = None,
                         limit: Optional[int] = None, encoding: Optional[str] = None, lang: str = 'en') -> int:
    """
    Write a member to a binary file object, in chunks as it is decoded.

    :param archive_file: The path of the archive, or of one of its volumes.
    :type archive_file: str
    :param file_in_archive: The path of the member in the archive.
    :type file_in_archive: str
    :param bin_file: The binary file object to write to.
    :type bin_file: BinaryIO
    :param password: Passwords to try (a ``str``, ``bytes`` or a list of them), defaults to ``None``.
    :type password: Union[str, bytes, Iterable[Union[str, bytes]]], optional
    :param limit: Return only the first bytes: only the part of the archive that holds them is fetched, and the CRC cannot be checked,
        defaults to ``None``.
    :type limit: int, optional
    :param encoding: Encoding of the names that are not Unicode (``shift_jis``, ``gbk``, ``ibm866``, ...), defaults to ``None`` (guessed).
    :type encoding: str, optional
    :param lang: Hint for guessing that encoding (``'ru'``, ``'ja'``, ...), defaults to ``'en'``.
    :type lang: str, optional
    :return: The number of bytes written.
    :rtype: int
    :raises hfutils.index.zip.errors.ZipArchiveNotFound: If the archive does not exist (a :class:`FileNotFoundError` too).
    :raises hfutils.index.zip.errors.NotAZipError: If it is not a zip (``err.detected`` says what it looks like).
    :raises hfutils.index.zip.errors.ZipVolumeError: If a volume of a split archive is missing.
    :raises FileNotFoundError: If there is no such member.
    :raises hfutils.index.zip.errors.ZipPasswordRequiredError: If the member is encrypted and there is no password.
    :raises hfutils.index.zip.errors.ZipPasswordError: If no password opens it.
    :raises hfutils.index.zip.errors.ZipUnsupportedError: If the method or the encryption is not supported.
    :raises hfutils.index.zip.errors.ZipFormatError: If the data is damaged (size or CRC do not match).

    Example::

        >>> import io
        >>> from hfutils.index import zip_file_write_bytes
        >>> buffer = io.BytesIO()
        >>> zip_file_write_bytes('archive.zip', 'hello.txt', buffer)
        27
        >>> buffer.getvalue()
        b'hello from the zip fixture\\n'
    """
    return write_member(_open(archive_file, password, encoding, lang), file_in_archive, bin_file, password, limit)


def zip_file_download(archive_file: str, file_in_archive: str, local_file: str, password: PasswordTyping = None,
                      encoding: Optional[str] = None, lang: str = 'en') -> None:
    """
    Extract a member to a local file.

    The member is written to a temporary file next to ``local_file`` and moved into place when it is complete, so a failed check (CRC,
    password) leaves nothing behind.

    :param archive_file: The path of the archive, or of one of its volumes.
    :type archive_file: str
    :param file_in_archive: The path of the member in the archive.
    :type file_in_archive: str
    :param local_file: The file to write; its directory is created.
    :type local_file: str
    :param password: Passwords to try (a ``str``, ``bytes`` or a list of them), defaults to ``None``.
    :type password: Union[str, bytes, Iterable[Union[str, bytes]]], optional
    :param encoding: Encoding of the names that are not Unicode (``shift_jis``, ``gbk``, ``ibm866``, ...), defaults to ``None`` (guessed).
    :type encoding: str, optional
    :param lang: Hint for guessing that encoding (``'ru'``, ``'ja'``, ...), defaults to ``'en'``.
    :type lang: str, optional
    :return: ``None``.
    :rtype: None
    :raises hfutils.index.zip.errors.ZipArchiveNotFound: If the archive does not exist (a :class:`FileNotFoundError` too).
    :raises hfutils.index.zip.errors.NotAZipError: If it is not a zip (``err.detected`` says what it looks like).
    :raises hfutils.index.zip.errors.ZipVolumeError: If a volume of a split archive is missing.
    :raises FileNotFoundError: If there is no such member.
    :raises hfutils.index.zip.errors.ZipPasswordRequiredError: If the member is encrypted and there is no password.
    :raises hfutils.index.zip.errors.ZipPasswordError: If no password opens it.
    :raises hfutils.index.zip.errors.ZipUnsupportedError: If the method or the encryption is not supported.
    :raises hfutils.index.zip.errors.ZipFormatError: If the data is damaged (size or CRC do not match).

    Example::

        >>> from hfutils.index import zip_file_download
        >>> zip_file_download('archive.zip', 'docs/readme.md', 'out/readme.md')
        >>> open('out/readme.md', 'rb').read()
        b'# Fixture\\n\\nNested markdown member.\\n'
    """
    download_member(_open(archive_file, password, encoding, lang), file_in_archive, local_file, password)


def zip_cache_reset(maxsize: Optional[int] = None):
    """
    Forget the directories read so far.

    :param maxsize: The new size of the cache, defaults to ``None`` (unchanged).
    :type maxsize: int, optional
    :return: ``None``.
    :rtype: None

    Example::

        >>> from hfutils.index import zip_cache_reset
        >>> zip_cache_reset()
        >>> zip_cache_reset(maxsize=16)
    """
    global _cache
    _cache = LRUCache(maxsize=maxsize or _cache.maxsize)

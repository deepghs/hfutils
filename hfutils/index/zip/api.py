"""
What the local (:mod:`hfutils.index.zip.local`) and the remote (:mod:`hfutils.index.zip.fetch`) functions have in common: the shape of
the answers and the ways to write a member out.

The module contains:

* :func:`entry_info`, :func:`index_info` - the dictionaries the public functions return
* :func:`write_member`, :func:`download_member` - write a member to a file object, or to a file

Example::

    >>> from hfutils.index.zip.directory import open_zip
    >>> from hfutils.index.zip.reader import ZipArchive
    >>> from hfutils.index.zip.source import FileSource
    >>> archive = ZipArchive(open_zip('archive.zip', FileSource))
    >>> from hfutils.index.zip.api import entry_info
    >>> entry_info(archive, 'hello.txt')['size']
    27
"""
import os
import shutil
from typing import BinaryIO, Dict, Optional

from .codecs import method_name
from .reader import ZipArchive, PasswordTyping


def entry_info(archive: ZipArchive, path: str) -> Dict:
    """
    The information about one member.

    :param archive: The opened archive.
    :type archive: ZipArchive
    :param path: The path of the member.
    :type path: str
    :return: A dictionary with ``name``, ``path``, ``size``, ``compressed_size``, ``crc32``, ``method``, ``method_name``, ``encrypted``,
        ``offset`` and ``volume``.
    :rtype: Dict
    :raises FileNotFoundError: If there is no such member.

    Example::

        >>> from hfutils.index.zip.directory import open_zip
        >>> from hfutils.index.zip.reader import ZipArchive
        >>> from hfutils.index.zip.source import FileSource
        >>> archive = ZipArchive(open_zip('archive.zip', FileSource))
        >>> from hfutils.index.zip.api import entry_info
        >>> info = entry_info(archive, 'hello.txt')
        >>> info['method_name'], info['volume']
        ('bzip2', 0)
    """
    e = archive.entry(path)
    return {
        'name': e.name,
        'path': e.path,
        'size': e.size,
        'compressed_size': e.csize,
        'crc32': e.crc,
        'method': e.method,
        'method_name': method_name(e.method),
        'encrypted': e.encrypted,
        'offset': e.offset,
        'volume': e.disk,
    }


def index_info(archive: ZipArchive) -> Dict:
    """
    The information about a whole archive.

    :param archive: The opened archive.
    :type archive: ZipArchive
    :return: A dictionary with ``files`` (:func:`entry_info` of every file by path), ``archive_size``, ``encoding``, ``volumes``,
        ``comment``, ``encrypted`` and ``notes``.
    :rtype: Dict

    Example::

        >>> from hfutils.index.zip.directory import open_zip
        >>> from hfutils.index.zip.reader import ZipArchive
        >>> from hfutils.index.zip.source import FileSource
        >>> archive = ZipArchive(open_zip('archive.zip', FileSource))
        >>> from hfutils.index.zip.api import index_info
        >>> sorted(index_info(archive))
        ['archive_size', 'comment', 'encoding', 'encrypted', 'files', 'notes', 'volumes']
    """
    d = archive.directory
    return {
        'files': {p: entry_info(archive, p) for p in d.files},
        'archive_size': d.source.size,
        'encoding': d.encoding,
        'volumes': list(d.volumes),
        'comment': d.comment.decode('utf-8', 'replace'),
        'encrypted': archive.encrypted,
        'notes': list(d.notes),
    }


def write_member(archive: ZipArchive, path: str, bin_file: BinaryIO, password: PasswordTyping = None,
                 limit: Optional[int] = None) -> int:
    """
    Stream a member into a file object.

    :param archive: The opened archive.
    :type archive: ZipArchive
    :param path: The path of the member.
    :type path: str
    :param bin_file: The binary file object to write to.
    :type bin_file: BinaryIO
    :param password: Passwords to try, defaults to ``None``.
    :type password: Union[str, bytes, Iterable[Union[str, bytes]]], optional
    :param limit: Write only the first bytes, defaults to ``None``.
    :type limit: int, optional
    :return: The number of bytes written.
    :rtype: int
    :raises FileNotFoundError: If there is no such member.
    :raises hfutils.index.zip.errors.ZipIndexError: If the member cannot be read, see :meth:`ZipArchive.iter_chunks`.

    Example::

        >>> from hfutils.index.zip.directory import open_zip
        >>> from hfutils.index.zip.reader import ZipArchive
        >>> from hfutils.index.zip.source import FileSource
        >>> archive = ZipArchive(open_zip('archive.zip', FileSource))
        >>> import io
        >>> from hfutils.index.zip.api import write_member
        >>> buffer = io.BytesIO()
        >>> write_member(archive, 'hello.txt', buffer, limit=5), buffer.getvalue()
        (5, b'hello')
    """
    total = 0
    for chunk in archive.iter_chunks(path, limit=limit, password=password):
        bin_file.write(chunk)
        total += len(chunk)
    return total


def download_member(archive: ZipArchive, path: str, local_file: str, password: PasswordTyping = None) -> None:
    """
    Write a member to a file through a temporary one, so that a failed check (CRC, password) leaves nothing behind.

    :param archive: The opened archive.
    :type archive: ZipArchive
    :param path: The path of the member.
    :type path: str
    :param local_file: The file to write; its directory is created.
    :type local_file: str
    :param password: Passwords to try, defaults to ``None``.
    :type password: Union[str, bytes, Iterable[Union[str, bytes]]], optional
    :return: ``None``.
    :rtype: None
    :raises FileNotFoundError: If there is no such member.
    :raises hfutils.index.zip.errors.ZipIndexError: If the member cannot be read, see :meth:`ZipArchive.iter_chunks`.

    Example::

        >>> from hfutils.index.zip.directory import open_zip
        >>> from hfutils.index.zip.reader import ZipArchive
        >>> from hfutils.index.zip.source import FileSource
        >>> archive = ZipArchive(open_zip('archive.zip', FileSource))
        >>> from hfutils.index.zip.api import download_member
        >>> download_member(archive, 'hello.txt', 'out/hello.txt')
        >>> open('out/hello.txt', 'rb').read()
        b'hello from the zip fixture\\n'
    """
    directory = os.path.dirname(os.path.abspath(local_file))
    os.makedirs(directory, exist_ok=True)
    tmp = f'{local_file}.part-{os.getpid()}'
    try:
        with open(tmp, 'wb') as f:
            write_member(archive, path, f, password)
        shutil.move(tmp, local_file)
    finally:
        if os.path.exists(tmp):
            os.remove(tmp)

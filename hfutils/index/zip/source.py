"""
Where the bytes of a zip come from.

Every source answers one question, ``fetch(start, length)``, whatever is behind it: a local file, memory, the concatenation of
volumes, or Range requests to a Hugging Face repository.

The module contains:

* :class:`ZipSource` - the interface, with ``size``, ``name`` and the size of a streaming ``window``
* :class:`BytesSource`, :class:`FileSource` - memory and a local file
* :class:`ConcatSource` - volumes read as one file, or addressed by ``base[disk] + offset``
* :class:`HfSource` - a file of a Hugging Face repository

Example::

    >>> from hfutils.index.zip.source import BytesSource, ConcatSource
    >>> source = ConcatSource([BytesSource(b'abc'), BytesSource(b'def')])
    >>> source.size, source.fetch(2, 3)
    (6, b'cde')
"""
import io
import os
from typing import List, Optional, Dict, Union, Sequence

from huggingface_hub.file_download import http_get, hf_hub_url
from huggingface_hub.utils import build_hf_headers

from .errors import ZipFetchError


class ZipSource:
    """
    A random access byte source with a known size.

    :ivar size: The number of bytes in the source.
    :vartype size: int
    :ivar name: A name for error messages (a path, ``dataset:owner/repo/file``).
    :vartype name: str
    :ivar window: How much a streaming read asks for at a time.
    :vartype window: int

    Example::

        >>> from hfutils.index.zip.source import BytesSource
        >>> source = BytesSource(b'0123456789')
        >>> source.size, source.window
        (10, 1048576)
    """
    size: int = 0
    name: str = ''
    window: int = 1 << 20

    def fetch(self, start: int, length: int) -> bytes:
        """
        Read exactly ``length`` bytes from ``start``. Subclasses implement this.

        :param start: Offset of the first byte.
        :type start: int
        :param length: Number of bytes.
        :type length: int
        :return: The bytes.
        :rtype: bytes
        :raises NotImplementedError: On the interface itself.

        Example::

            >>> from hfutils.index.zip.source import ZipSource
            >>> try:
            ...     ZipSource().fetch(0, 1)
            ... except NotImplementedError:
            ...     print('subclasses implement it')
            subclasses implement it
        """
        raise NotImplementedError

    def fetch_range(self, start: int, length: int) -> bytes:
        """
        Read like :meth:`fetch`, clipped to the source: reading past the end returns what is there.

        :param start: Offset of the first byte.
        :type start: int
        :param length: Number of bytes asked for.
        :type length: int
        :return: The bytes, fewer than ``length`` at the end, empty past it.
        :rtype: bytes

        Example::

            >>> from hfutils.index.zip.source import BytesSource
            >>> source = BytesSource(b'0123456789')
            >>> source.fetch_range(8, 100), source.fetch_range(20, 5)
            (b'89', b'')
        """
        length = max(0, min(length, self.size - start))
        return self.fetch(start, length) if length > 0 else b''


class BytesSource(ZipSource):
    """
    A source over bytes in memory.

    :param data: The content.
    :type data: bytes
    :param name: The name used in error messages, defaults to ``'<memory>'``.
    :type name: str, optional

    Example::

        >>> from hfutils.index.zip.source import BytesSource
        >>> BytesSource(b'0123456789').fetch(2, 3)
        b'234'
    """
    def __init__(self, data: bytes, name: str = '<memory>'):
        """
        Build the source.

        :param data: The content.
        :type data: bytes
        :param name: The name used in error messages, defaults to ``'<memory>'``.
        :type name: str, optional
        :return: ``None``.
        :rtype: None
        """
        self.data, self.size, self.name = bytes(data), len(data), name

    def fetch(self, start: int, length: int) -> bytes:
        """
        Read ``length`` bytes from ``start``.

        :param start: Offset of the first byte.
        :type start: int
        :param length: Number of bytes.
        :type length: int
        :return: The bytes.
        :rtype: bytes

        Example::

            >>> from hfutils.index.zip.source import BytesSource
            >>> BytesSource(b'0123456789').fetch(0, 4)
            b'0123'
        """
        return self.data[start:start + length]


class FileSource(ZipSource):
    """
    A source over a local file, opened for every read so that nothing stays open.

    :param path: The file.
    :type path: str

    Example::

        >>> from hfutils.index.zip.source import FileSource
        >>> source = FileSource('archive.zip')
        >>> source.fetch(0, 4)
        b'PK\\x03\\x04'
    """
    def __init__(self, path: str):
        """
        Build the source.

        :param path: The file.
        :type path: str
        :return: ``None``.
        :rtype: None
        :raises FileNotFoundError: If the file does not exist.
        """
        self.path, self.name = path, path
        self.size = os.path.getsize(path)

    def fetch(self, start: int, length: int) -> bytes:
        """
        Read ``length`` bytes from ``start``.

        :param start: Offset of the first byte.
        :type start: int
        :param length: Number of bytes.
        :type length: int
        :return: The bytes.
        :rtype: bytes

        Example::

            >>> from hfutils.index.zip.source import FileSource
            >>> FileSource('archive.zip').fetch_range(0, 2)
            b'PK'
        """
        with open(self.path, 'rb') as f:
            f.seek(start)
            return f.read(length)


class ConcatSource(ZipSource):
    """
    Volumes read as one file (a raw split), or addressed by ``bases[disk] + offset`` (an Info-ZIP disk set).

    :param parts: The volumes, in order.
    :type parts: Sequence[ZipSource]

    :ivar parts: The volumes.
    :vartype parts: List[ZipSource]
    :ivar bases: The offset of every volume in the concatenation.
    :vartype bases: List[int]

    Example::

        >>> from hfutils.index.zip.source import BytesSource, ConcatSource
        >>> source = ConcatSource([BytesSource(b'abc'), BytesSource(b'def')])
        >>> source.bases, source.fetch(1, 4)
        ([0, 3], b'bcde')
    """

    def __init__(self, parts: Sequence[ZipSource]):
        """
        Build the source.

        :param parts: The volumes, in order.
        :type parts: Sequence[ZipSource]
        :return: ``None``.
        :rtype: None
        """
        self.parts = list(parts)
        self.bases: List[int] = []
        total = 0
        for part in self.parts:
            self.bases.append(total)
            total += part.size
        self.size = total
        self.name = self.parts[0].name if self.parts else ''
        self.window = max((p.window for p in self.parts), default=1 << 20)

    def fetch(self, start: int, length: int) -> bytes:
        """
        Read ``length`` bytes from ``start`` of the concatenation, across volumes.

        :param start: Offset of the first byte in the concatenation.
        :type start: int
        :param length: Number of bytes.
        :type length: int
        :return: The bytes.
        :rtype: bytes

        Example::

            >>> from hfutils.index.zip.source import BytesSource, ConcatSource
            >>> ConcatSource([BytesSource(b'ab'), BytesSource(b'cd'), BytesSource(b'ef')]).fetch(1, 4)
            b'bcde'
        """
        out, end = [], start + length
        for base, part in zip(self.bases, self.parts):
            lo, hi = max(start, base), min(end, base + part.size)
            if lo < hi:
                out.append(part.fetch(lo - base, hi - lo))
        return b''.join(out)


class HfSource(ZipSource):
    """
    A file of a Hugging Face repository, read with Range requests (through ``http_get``, like the tar readers).

    :param repo_id: The repository.
    :type repo_id: str
    :param path: The file in the repository.
    :type path: str
    :param size: The size of the file (the Hub answers it with ``get_paths_info``).
    :type size: int
    :param repo_type: Type of the repository, defaults to ``'dataset'``.
    :type repo_type: str, optional
    :param revision: Revision of the repository, defaults to ``'main'``.
    :type revision: str, optional
    :param endpoint: The endpoint of the Hub, defaults to ``None`` (the default one).
    :type endpoint: str, optional
    :param hf_token: Access token, defaults to ``None`` (``$HF_TOKEN``).
    :type hf_token: str, optional
    :param proxies: Proxies for the requests, defaults to ``None``.
    :type proxies: Dict, optional
    :param user_agent: User agent of the requests, defaults to ``None``.
    :type user_agent: Union[Dict, str], optional
    :param headers: Extra headers, defaults to ``None``.
    :type headers: Dict[str, str], optional

    :ivar requests: How many requests this source has made.
    :vartype requests: int

    Example::

        >>> from hfutils.index.zip.source import HfSource
        >>> source = HfSource('owner/repo', 'archive.zip', size=100)
        >>> source.name, source.window
        ('dataset:owner/repo/archive.zip', 8388608)
    """
    window = 8 << 20

    def __init__(self, repo_id: str, path: str, size: int, repo_type: str = 'dataset', revision: str = 'main',
                 endpoint: Optional[str] = None, hf_token: Optional[str] = None, proxies: Optional[Dict] = None,
                 user_agent: Union[Dict, str, None] = None, headers: Optional[Dict[str, str]] = None):
        """
        Build the source (nothing is requested yet).

        :param repo_id: The repository.
        :type repo_id: str
        :param path: The file in the repository.
        :type path: str
        :param size: The size of the file.
        :type size: int
        :param repo_type: Type of the repository, defaults to ``'dataset'``.
        :type repo_type: str, optional
        :param revision: Revision of the repository, defaults to ``'main'``.
        :type revision: str, optional
        :param endpoint: The endpoint of the Hub, defaults to ``None``.
        :type endpoint: str, optional
        :param hf_token: Access token, defaults to ``None``.
        :type hf_token: str, optional
        :param proxies: Proxies for the requests, defaults to ``None``.
        :type proxies: Dict, optional
        :param user_agent: User agent of the requests, defaults to ``None``.
        :type user_agent: Union[Dict, str], optional
        :param headers: Extra headers, defaults to ``None``.
        :type headers: Dict[str, str], optional
        :return: ``None``.
        :rtype: None
        """
        self.repo_id, self.path, self.size, self.repo_type, self.revision = repo_id, path, size, repo_type, revision
        self.endpoint, self.hf_token, self.proxies, self.user_agent, self.headers = endpoint, hf_token, proxies, user_agent, headers
        self.name = f'{repo_type}:{repo_id}/{path}'
        self.requests = 0

    def _headers(self) -> Dict[str, str]:
        try:
            return build_hf_headers(token=self.hf_token, library_name=None, library_version=None, user_agent=self.user_agent,
                                    headers=self.headers)
        except TypeError:  # huggingface_hub 0.20 has no `headers` parameter
            headers = build_hf_headers(token=self.hf_token, library_name=None, library_version=None, user_agent=self.user_agent)
            headers.update(self.headers or {})
            return headers

    def fetch(self, start: int, length: int) -> bytes:
        """
        Read ``length`` bytes from ``start`` with one Range request.

        :param start: Offset of the first byte.
        :type start: int
        :param length: Number of bytes.
        :type length: int
        :return: The bytes.
        :rtype: bytes
        :raises hfutils.index.zip.errors.ZipFetchError: If the request fails (its ``status`` is the HTTP status when there was one) or the
            answer has not the length that was asked for.

        Example::

            >>> from hfutils.index.zip.source import HfSource
            >>> HfSource('owner/repo', 'archive.zip', size=100).fetch(0, 4)
            b'PK\\x03\\x04'
        """
        from ..fetch import _http_get_optional_kwargs
        url = hf_hub_url(self.repo_id, self.path, repo_type=self.repo_type, revision=self.revision, endpoint=self.endpoint)
        headers = self._headers()
        headers['Range'] = f'bytes={start}-{start + length - 1}'
        buf = io.BytesIO()
        self.requests += 1
        try:
            http_get(url, buf, proxies=self.proxies, resume_size=0, headers=headers, expected_size=length,
                     **_http_get_optional_kwargs(displayed_filename=self.path))
        except Exception as err:
            response = getattr(err, 'response', None)
            status = getattr(response, 'status_code', None)
            raise ZipFetchError(f'Cannot fetch bytes {start}-{start + length - 1} of {self.name}: {err}', status=status) from err
        data = buf.getvalue()
        if len(data) != length:
            raise ZipFetchError(f'Asked for {length} bytes of {self.name} at {start}, got {len(data)}.')
        return data

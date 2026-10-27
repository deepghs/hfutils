"""
Random access to the members of a zip stored in a Hugging Face repository, the counterpart of :mod:`hfutils.index.fetch` for tar archives.

Only the bytes that are needed travel: the end of the file (the directory), then the compressed bytes of the member, with ``Range``
requests, through the same ``http_get`` the tar functions use. The directory is cached per revision of the file (a ``get_paths_info``
request checks that it is still the one), so a second read costs one request for the member and none for the directory. The cache
holds entries only: the token, the proxies and the passwords of a call are never kept for another. Split archives work as well: any
volume of ``X.zip.001`` or ``X.z01`` / ``X.zip`` opens the whole set.

The first two arguments of every function are ``repo_id`` and ``archive_in_repo``; ``hf_token``, ``revision``, ``endpoint`` and
``repo_type`` mean what they mean in the tar functions, ``password`` / ``encoding`` / ``lang`` what they mean in
:mod:`hfutils.index.zip.local`.

The module contains:

* :func:`hf_zip_get_index`, :func:`hf_zip_list_files`, :func:`hf_zip_file_exists`, :func:`hf_zip_file_info`, :func:`hf_zip_file_size` - the directory
* :func:`hf_zip_file_read`, :func:`hf_zip_file_write_bytes`, :func:`hf_zip_file_download` - the members
* :func:`hf_zip_cache_reset` - forget the directories read so far

Example::

    >>> from hfutils.index import hf_zip_list_files, hf_zip_file_read
    >>> hf_zip_list_files('owner/repo', 'archive.zip')
    ['hello.txt', 'data/table.csv', 'docs/readme.md', 'images/noise.jpg']
    >>> hf_zip_file_read('owner/repo', 'archive.zip', 'hello.txt')
    b'hello from the zip fixture\\n'
"""
from dataclasses import replace
from typing import BinaryIO, Dict, List, Optional, Union

from cachetools import LRUCache

from ...operate.base import RepoTypeTyping, get_hf_client
from .api import entry_info, index_info, write_member, download_member
from .directory import open_zip, _RAW_VOLUME, _DISK_VOLUME
from .errors import ZipFetchError
from .reader import ZipArchive, PasswordTyping
from .source import HfSource, ConcatSource

_cache = LRUCache(maxsize=128)
_BATCH = 16


def _identity(info) -> tuple:
    """What changes when the file changes: the LFS sha256 (or the blob id of a small file) and the size."""
    lfs = getattr(info, 'lfs', None)
    sha = lfs.get('sha256') if isinstance(lfs, dict) else getattr(lfs, 'sha256', None)
    return sha or getattr(info, 'blob_id', None), info.size


class _Repo:
    """The files of one repository that an archive can be made of, looked up in batches (one request answers 16 names)."""

    def __init__(self, repo_id: str, repo_type: str, revision: str, hf_token: Optional[str], endpoint: Optional[str],
                 proxies: Optional[Dict], user_agent, headers):
        self.repo_id, self.repo_type, self.revision = repo_id, repo_type, revision
        self.hf_token, self.endpoint, self.proxies, self.user_agent, self.headers = hf_token, endpoint, proxies, user_agent, headers
        self.known: Dict[str, Optional[object]] = {}
        self.sources: Dict[str, HfSource] = {}

    def _candidates(self, name: str) -> List[str]:
        raw = _RAW_VOLUME.match(name)
        disk = _DISK_VOLUME.match(name)
        out = [name]
        if raw:
            n = int(raw.group('n'))
            out += [f'{raw.group("base")}.{k:03d}' for k in range(n + 1, n + _BATCH)]
        elif disk:
            width, n = len(disk.group('n')), int(disk.group('n'))
            out += [f'{disk.group("base")}.z{k:0{width}d}' for k in range(n + 1, n + _BATCH)]
        stem = name.rsplit('.', 1)[0]
        if name == stem + '.zip' or name.lower().endswith('.zip'):
            out += [f'{stem}.z{k:02d}' for k in range(1, _BATCH)]
        return [c for c in dict.fromkeys(out) if c not in self.known]

    def lookup(self, name: str):
        if name not in self.known:
            paths = self._candidates(name)
            try:
                found = get_hf_client(self.hf_token).get_paths_info(
                    self.repo_id, paths, repo_type=self.repo_type, revision=self.revision)
            except Exception as err:
                response = getattr(err, 'response', None)
                if getattr(response, 'status_code', None) == 404 or type(err).__name__ in (
                        'RepositoryNotFoundError', 'RevisionNotFoundError', 'EntryNotFoundError'):
                    raise
                raise ZipFetchError(f'Cannot look up {paths[0]} in {self.repo_type} {self.repo_id}: {err}',
                                    status=getattr(response, 'status_code', None)) from err
            by_path = {f.path: f for f in found if getattr(f, 'size', None) is not None}
            for p in paths:
                self.known[p] = by_path.get(p)
        info = self.known.get(name)
        return info

    def source(self, name: str) -> Optional[HfSource]:
        info = self.lookup(name)
        if info is None:
            return None
        if name not in self.sources:
            self.sources[name] = HfSource(self.repo_id, name, info.size, repo_type=self.repo_type, revision=self.revision,
                                          endpoint=self.endpoint, hf_token=self.hf_token, proxies=self.proxies,
                                          user_agent=self.user_agent, headers=self.headers)
        return self.sources[name]


def _open(repo_id: str, archive_in_repo: str, password: PasswordTyping, encoding: Optional[str], lang: str, repo_type: str,
          revision: str, hf_token: Optional[str], endpoint: Optional[str], proxies: Optional[Dict], user_agent,
          headers: Optional[Dict[str, str]], no_cache: bool = False) -> ZipArchive:
    repo = _Repo(repo_id, repo_type, revision, hf_token, endpoint, proxies, user_agent, headers)
    # Not the token, the proxies or the headers: a cached directory is only entries, its sources are made again for every caller.
    key = (endpoint, repo_type, repo_id, revision, archive_in_repo, encoding, lang)
    cached = None if no_cache else _cache.get(key)
    if cached is not None:
        directory, identities = cached
        found = get_hf_client(hf_token).get_paths_info(repo_id, list(identities), repo_type=repo_type, revision=revision)
        if {f.path: _identity(f) for f in found if getattr(f, 'size', None) is not None} == identities:
            for f in found:
                repo.known[f.path] = f
            parts = [repo.source(name) for name in directory.volumes]
            return ZipArchive(replace(directory, source=parts[0] if len(parts) == 1 else ConcatSource(parts)), password)
    directory = open_zip(archive_in_repo, repo.source, encoding=encoding, lang=lang)
    if not no_cache:
        identities = {name: _identity(repo.known[name]) for name in directory.volumes}
        _cache[key] = (replace(directory, source=None), identities)
    return ZipArchive(directory, password)


def hf_zip_get_index(repo_id: str, archive_in_repo: str, repo_type: RepoTypeTyping = 'dataset', revision: str = 'main',
                     encoding: Optional[str] = None, lang: str = 'en', proxies: Optional[Dict] = None,
                     user_agent: Union[Dict, str, None] = None, headers: Optional[Dict[str, str]] = None,
                     endpoint: Optional[str] = None, hf_token: Optional[str] = None, no_cache: bool = False) -> Dict:
    """
    Read the directory of a zip archive in a repository.

    The answer is ``{'files': {path: info}, 'encoding', 'volumes', 'comment', 'encrypted', 'notes', 'archive_size'}``, see
    :func:`hfutils.index.zip.local.zip_get_index`. Only the end of the archive is read (one ``Range`` request in the usual case).

    :param repo_id: The repository, e.g. ``owner/name``.
    :type repo_id: str
    :param archive_in_repo: The path of the archive in the repository, or of one of its volumes.
    :type archive_in_repo: str
    :param repo_type: Type of the repository, defaults to ``'dataset'``.
    :type repo_type: RepoTypeTyping, optional
    :param revision: Revision of the repository, defaults to ``'main'``.
    :type revision: str, optional
    :param encoding: Encoding of the names that are not Unicode (``shift_jis``, ``gbk``, ``ibm866``, ...), defaults to ``None`` (guessed).
    :type encoding: str, optional
    :param lang: Hint for guessing that encoding (``'ru'``, ``'ja'``, ...), defaults to ``'en'``.
    :type lang: str, optional
    :param proxies: Proxies for the requests, defaults to ``None``.
    :type proxies: Dict, optional
    :param user_agent: User agent of the requests, defaults to ``None``.
    :type user_agent: Union[Dict, str], optional
    :param headers: Extra headers for the requests, defaults to ``None``.
    :type headers: Dict[str, str], optional
    :param endpoint: The endpoint of the Hub, defaults to ``None`` (the default one).
    :type endpoint: str, optional
    :param hf_token: Access token, defaults to ``None`` (``$HF_TOKEN``).
    :type hf_token: str, optional
    :param no_cache: Read the directory again even if it is cached, defaults to ``False``.
    :type no_cache: bool, optional
    :return: The directory.
    :rtype: Dict
    :raises hfutils.index.zip.errors.ZipArchiveNotFound: If the archive does not exist in the repository.
    :raises hfutils.index.zip.errors.NotAZipError: If it is not a zip (``err.detected`` says what it looks like:
        ``'git-lfs-pointer'``, ``'html'``, ``'tar'``, ...).
    :raises hfutils.index.zip.errors.ZipVolumeError: If a volume of a split archive is missing from the repository.
    :raises hfutils.index.zip.errors.ZipFetchError: If the bytes cannot be fetched (``err.status`` is the HTTP status when there was one).

    Example::

        >>> from hfutils.index import hf_zip_get_index
        >>> index = hf_zip_get_index('owner/repo', 'archive.zip')
        >>> index['files']['hello.txt']['size'], index['volumes']
        (27, ['archive.zip'])
    """
    return index_info(_open(repo_id, archive_in_repo, None, encoding, lang, repo_type, revision, hf_token, endpoint, proxies,
                            user_agent, headers, no_cache))


def hf_zip_list_files(repo_id: str, archive_in_repo: str, repo_type: RepoTypeTyping = 'dataset', revision: str = 'main',
                      encoding: Optional[str] = None, lang: str = 'en', proxies: Optional[Dict] = None,
                      user_agent: Union[Dict, str, None] = None, headers: Optional[Dict[str, str]] = None,
                      endpoint: Optional[str] = None, hf_token: Optional[str] = None, no_cache: bool = False) -> List[str]:
    """
    List the files of the archive, see :func:`hfutils.index.zip.local.zip_list_files`.

    :param repo_id: The repository, e.g. ``owner/name``.
    :type repo_id: str
    :param archive_in_repo: The path of the archive in the repository, or of one of its volumes.
    :type archive_in_repo: str
    :param repo_type: Type of the repository, defaults to ``'dataset'``.
    :type repo_type: RepoTypeTyping, optional
    :param revision: Revision of the repository, defaults to ``'main'``.
    :type revision: str, optional
    :param encoding: Encoding of the names that are not Unicode (``shift_jis``, ``gbk``, ``ibm866``, ...), defaults to ``None`` (guessed).
    :type encoding: str, optional
    :param lang: Hint for guessing that encoding (``'ru'``, ``'ja'``, ...), defaults to ``'en'``.
    :type lang: str, optional
    :param proxies: Proxies for the requests, defaults to ``None``.
    :type proxies: Dict, optional
    :param user_agent: User agent of the requests, defaults to ``None``.
    :type user_agent: Union[Dict, str], optional
    :param headers: Extra headers for the requests, defaults to ``None``.
    :type headers: Dict[str, str], optional
    :param endpoint: The endpoint of the Hub, defaults to ``None`` (the default one).
    :type endpoint: str, optional
    :param hf_token: Access token, defaults to ``None`` (``$HF_TOKEN``).
    :type hf_token: str, optional
    :param no_cache: Read the directory again even if it is cached, defaults to ``False``.
    :type no_cache: bool, optional
    :return: The paths, in the order of the directory.
    :rtype: List[str]
    :raises hfutils.index.zip.errors.ZipArchiveNotFound: If the archive does not exist in the repository.
    :raises hfutils.index.zip.errors.NotAZipError: If it is not a zip (``err.detected`` says what it looks like:
        ``'git-lfs-pointer'``, ``'html'``, ``'tar'``, ...).
    :raises hfutils.index.zip.errors.ZipVolumeError: If a volume of a split archive is missing from the repository.
    :raises hfutils.index.zip.errors.ZipFetchError: If the bytes cannot be fetched (``err.status`` is the HTTP status when there was one).

    Example::

        >>> from hfutils.index import hf_zip_list_files
        >>> hf_zip_list_files('owner/repo', 'archive.zip')
        ['hello.txt', 'data/table.csv', 'docs/readme.md', 'images/noise.jpg']
    """
    return _open(repo_id, archive_in_repo, None, encoding, lang, repo_type, revision, hf_token, endpoint, proxies, user_agent,
                 headers, no_cache).paths()


def hf_zip_file_exists(repo_id: str, archive_in_repo: str, file_in_archive: str, repo_type: RepoTypeTyping = 'dataset',
                       revision: str = 'main', encoding: Optional[str] = None, lang: str = 'en',
                       proxies: Optional[Dict] = None, user_agent: Union[Dict, str, None] = None,
                       headers: Optional[Dict[str, str]] = None, endpoint: Optional[str] = None,
                       hf_token: Optional[str] = None) -> bool:
    """
    Tell whether the archive has a file of that path.

    :param repo_id: The repository, e.g. ``owner/name``.
    :type repo_id: str
    :param archive_in_repo: The path of the archive in the repository, or of one of its volumes.
    :type archive_in_repo: str
    :param file_in_archive: The path of the member in the archive.
    :type file_in_archive: str
    :param repo_type: Type of the repository, defaults to ``'dataset'``.
    :type repo_type: RepoTypeTyping, optional
    :param revision: Revision of the repository, defaults to ``'main'``.
    :type revision: str, optional
    :param encoding: Encoding of the names that are not Unicode (``shift_jis``, ``gbk``, ``ibm866``, ...), defaults to ``None`` (guessed).
    :type encoding: str, optional
    :param lang: Hint for guessing that encoding (``'ru'``, ``'ja'``, ...), defaults to ``'en'``.
    :type lang: str, optional
    :param proxies: Proxies for the requests, defaults to ``None``.
    :type proxies: Dict, optional
    :param user_agent: User agent of the requests, defaults to ``None``.
    :type user_agent: Union[Dict, str], optional
    :param headers: Extra headers for the requests, defaults to ``None``.
    :type headers: Dict[str, str], optional
    :param endpoint: The endpoint of the Hub, defaults to ``None`` (the default one).
    :type endpoint: str, optional
    :param hf_token: Access token, defaults to ``None`` (``$HF_TOKEN``).
    :type hf_token: str, optional
    :return: ``True`` when it has.
    :rtype: bool
    :raises hfutils.index.zip.errors.ZipArchiveNotFound: If the archive does not exist in the repository.
    :raises hfutils.index.zip.errors.NotAZipError: If it is not a zip (``err.detected`` says what it looks like:
        ``'git-lfs-pointer'``, ``'html'``, ``'tar'``, ...).
    :raises hfutils.index.zip.errors.ZipVolumeError: If a volume of a split archive is missing from the repository.
    :raises hfutils.index.zip.errors.ZipFetchError: If the bytes cannot be fetched (``err.status`` is the HTTP status when there was one).

    Example::

        >>> from hfutils.index import hf_zip_file_exists
        >>> hf_zip_file_exists('owner/repo', 'archive.zip', 'hello.txt'), hf_zip_file_exists('owner/repo', 'archive.zip', 'nope.txt')
        (True, False)
    """
    return file_in_archive in _open(repo_id, archive_in_repo, None, encoding, lang, repo_type, revision, hf_token, endpoint,
                                    proxies, user_agent, headers)


def hf_zip_file_info(repo_id: str, archive_in_repo: str, file_in_archive: str, repo_type: RepoTypeTyping = 'dataset',
                     revision: str = 'main', encoding: Optional[str] = None, lang: str = 'en', proxies: Optional[Dict] = None,
                     user_agent: Union[Dict, str, None] = None, headers: Optional[Dict[str, str]] = None,
                     endpoint: Optional[str] = None, hf_token: Optional[str] = None) -> Dict:
    """
    The record of a member, see :func:`hfutils.index.zip.local.zip_get_index` for its keys.

    :param repo_id: The repository, e.g. ``owner/name``.
    :type repo_id: str
    :param archive_in_repo: The path of the archive in the repository, or of one of its volumes.
    :type archive_in_repo: str
    :param file_in_archive: The path of the member in the archive.
    :type file_in_archive: str
    :param repo_type: Type of the repository, defaults to ``'dataset'``.
    :type repo_type: RepoTypeTyping, optional
    :param revision: Revision of the repository, defaults to ``'main'``.
    :type revision: str, optional
    :param encoding: Encoding of the names that are not Unicode (``shift_jis``, ``gbk``, ``ibm866``, ...), defaults to ``None`` (guessed).
    :type encoding: str, optional
    :param lang: Hint for guessing that encoding (``'ru'``, ``'ja'``, ...), defaults to ``'en'``.
    :type lang: str, optional
    :param proxies: Proxies for the requests, defaults to ``None``.
    :type proxies: Dict, optional
    :param user_agent: User agent of the requests, defaults to ``None``.
    :type user_agent: Union[Dict, str], optional
    :param headers: Extra headers for the requests, defaults to ``None``.
    :type headers: Dict[str, str], optional
    :param endpoint: The endpoint of the Hub, defaults to ``None`` (the default one).
    :type endpoint: str, optional
    :param hf_token: Access token, defaults to ``None`` (``$HF_TOKEN``).
    :type hf_token: str, optional
    :return: The information.
    :rtype: Dict
    :raises hfutils.index.zip.errors.ZipArchiveNotFound: If the archive does not exist in the repository.
    :raises hfutils.index.zip.errors.NotAZipError: If it is not a zip (``err.detected`` says what it looks like:
        ``'git-lfs-pointer'``, ``'html'``, ``'tar'``, ...).
    :raises hfutils.index.zip.errors.ZipVolumeError: If a volume of a split archive is missing from the repository.
    :raises hfutils.index.zip.errors.ZipFetchError: If the bytes cannot be fetched (``err.status`` is the HTTP status when there was one).
    :raises FileNotFoundError: If there is no such member.

    Example::

        >>> from hfutils.index import hf_zip_file_info
        >>> info = hf_zip_file_info('owner/repo', 'archive.zip', 'hello.txt')
        >>> info['size'], info['method_name']
        (27, 'bzip2')
    """
    return entry_info(_open(repo_id, archive_in_repo, None, encoding, lang, repo_type, revision, hf_token, endpoint, proxies,
                            user_agent, headers), file_in_archive)


def hf_zip_file_size(repo_id: str, archive_in_repo: str, file_in_archive: str, repo_type: RepoTypeTyping = 'dataset',
                     revision: str = 'main', encoding: Optional[str] = None, lang: str = 'en', proxies: Optional[Dict] = None,
                     user_agent: Union[Dict, str, None] = None, headers: Optional[Dict[str, str]] = None,
                     endpoint: Optional[str] = None, hf_token: Optional[str] = None) -> int:
    """
    The uncompressed size of a member.

    :param repo_id: The repository, e.g. ``owner/name``.
    :type repo_id: str
    :param archive_in_repo: The path of the archive in the repository, or of one of its volumes.
    :type archive_in_repo: str
    :param file_in_archive: The path of the member in the archive.
    :type file_in_archive: str
    :param repo_type: Type of the repository, defaults to ``'dataset'``.
    :type repo_type: RepoTypeTyping, optional
    :param revision: Revision of the repository, defaults to ``'main'``.
    :type revision: str, optional
    :param encoding: Encoding of the names that are not Unicode (``shift_jis``, ``gbk``, ``ibm866``, ...), defaults to ``None`` (guessed).
    :type encoding: str, optional
    :param lang: Hint for guessing that encoding (``'ru'``, ``'ja'``, ...), defaults to ``'en'``.
    :type lang: str, optional
    :param proxies: Proxies for the requests, defaults to ``None``.
    :type proxies: Dict, optional
    :param user_agent: User agent of the requests, defaults to ``None``.
    :type user_agent: Union[Dict, str], optional
    :param headers: Extra headers for the requests, defaults to ``None``.
    :type headers: Dict[str, str], optional
    :param endpoint: The endpoint of the Hub, defaults to ``None`` (the default one).
    :type endpoint: str, optional
    :param hf_token: Access token, defaults to ``None`` (``$HF_TOKEN``).
    :type hf_token: str, optional
    :return: The size in bytes.
    :rtype: int
    :raises hfutils.index.zip.errors.ZipArchiveNotFound: If the archive does not exist in the repository.
    :raises hfutils.index.zip.errors.NotAZipError: If it is not a zip (``err.detected`` says what it looks like:
        ``'git-lfs-pointer'``, ``'html'``, ``'tar'``, ...).
    :raises hfutils.index.zip.errors.ZipVolumeError: If a volume of a split archive is missing from the repository.
    :raises hfutils.index.zip.errors.ZipFetchError: If the bytes cannot be fetched (``err.status`` is the HTTP status when there was one).
    :raises FileNotFoundError: If there is no such member.

    Example::

        >>> from hfutils.index import hf_zip_file_size
        >>> hf_zip_file_size('owner/repo', 'archive.zip', 'hello.txt')
        27
    """
    return hf_zip_file_info(repo_id, archive_in_repo, file_in_archive, repo_type, revision, encoding, lang, proxies, user_agent,
                            headers, endpoint, hf_token)['size']


def hf_zip_file_read(repo_id: str, archive_in_repo: str, file_in_archive: str, password: PasswordTyping = None,
                     limit: Optional[int] = None, repo_type: RepoTypeTyping = 'dataset', revision: str = 'main',
                     encoding: Optional[str] = None, lang: str = 'en', proxies: Optional[Dict] = None,
                     user_agent: Union[Dict, str, None] = None, headers: Optional[Dict[str, str]] = None,
                     endpoint: Optional[str] = None, hf_token: Optional[str] = None) -> bytes:
    """
    The content of a member; with ``limit`` only the first bytes, and only the part of the archive that holds them is fetched.

    :param repo_id: The repository, e.g. ``owner/name``.
    :type repo_id: str
    :param archive_in_repo: The path of the archive in the repository, or of one of its volumes.
    :type archive_in_repo: str
    :param file_in_archive: The path of the member in the archive.
    :type file_in_archive: str
    :param password: Passwords to try (a ``str``, ``bytes`` or a list of them), defaults to ``None``.
    :type password: Union[str, bytes, Iterable[Union[str, bytes]]], optional
    :param limit: Return only the first bytes: only the part of the archive that holds them is fetched, and the CRC cannot be checked,
        defaults to ``None``.
    :type limit: int, optional
    :param repo_type: Type of the repository, defaults to ``'dataset'``.
    :type repo_type: RepoTypeTyping, optional
    :param revision: Revision of the repository, defaults to ``'main'``.
    :type revision: str, optional
    :param encoding: Encoding of the names that are not Unicode (``shift_jis``, ``gbk``, ``ibm866``, ...), defaults to ``None`` (guessed).
    :type encoding: str, optional
    :param lang: Hint for guessing that encoding (``'ru'``, ``'ja'``, ...), defaults to ``'en'``.
    :type lang: str, optional
    :param proxies: Proxies for the requests, defaults to ``None``.
    :type proxies: Dict, optional
    :param user_agent: User agent of the requests, defaults to ``None``.
    :type user_agent: Union[Dict, str], optional
    :param headers: Extra headers for the requests, defaults to ``None``.
    :type headers: Dict[str, str], optional
    :param endpoint: The endpoint of the Hub, defaults to ``None`` (the default one).
    :type endpoint: str, optional
    :param hf_token: Access token, defaults to ``None`` (``$HF_TOKEN``).
    :type hf_token: str, optional
    :return: The content.
    :rtype: bytes
    :raises hfutils.index.zip.errors.ZipArchiveNotFound: If the archive does not exist in the repository.
    :raises hfutils.index.zip.errors.NotAZipError: If it is not a zip (``err.detected`` says what it looks like:
        ``'git-lfs-pointer'``, ``'html'``, ``'tar'``, ...).
    :raises hfutils.index.zip.errors.ZipVolumeError: If a volume of a split archive is missing from the repository.
    :raises hfutils.index.zip.errors.ZipFetchError: If the bytes cannot be fetched (``err.status`` is the HTTP status when there was one).
    :raises FileNotFoundError: If there is no such member.
    :raises hfutils.index.zip.errors.ZipPasswordRequiredError: If the member is encrypted and there is no password.
    :raises hfutils.index.zip.errors.ZipPasswordError: If no password opens it.
    :raises hfutils.index.zip.errors.ZipUnsupportedError: If the method or the encryption is not supported.
    :raises hfutils.index.zip.errors.ZipFormatError: If the data is damaged (size or CRC do not match).

    Example::

        >>> from hfutils.index import hf_zip_file_read
        >>> hf_zip_file_read('owner/repo', 'archive.zip', 'hello.txt')
        b'hello from the zip fixture\\n'
        >>> hf_zip_file_read('owner/repo', 'locked.zip', 'hello.txt', password='secret', limit=5)
        b'hello'
    """
    return _open(repo_id, archive_in_repo, password, encoding, lang, repo_type, revision, hf_token, endpoint, proxies, user_agent,
                 headers).read(file_in_archive, limit=limit, password=password)


def hf_zip_file_write_bytes(repo_id: str, archive_in_repo: str, file_in_archive: str, bin_file: BinaryIO,
                            password: PasswordTyping = None, limit: Optional[int] = None, repo_type: RepoTypeTyping = 'dataset',
                            revision: str = 'main', encoding: Optional[str] = None, lang: str = 'en',
                            proxies: Optional[Dict] = None, user_agent: Union[Dict, str, None] = None,
                            headers: Optional[Dict[str, str]] = None, endpoint: Optional[str] = None,
                            hf_token: Optional[str] = None) -> int:
    """
    Write a member to a binary file object as it is decoded.

    :param repo_id: The repository, e.g. ``owner/name``.
    :type repo_id: str
    :param archive_in_repo: The path of the archive in the repository, or of one of its volumes.
    :type archive_in_repo: str
    :param file_in_archive: The path of the member in the archive.
    :type file_in_archive: str
    :param bin_file: The binary file object to write to.
    :type bin_file: BinaryIO
    :param password: Passwords to try (a ``str``, ``bytes`` or a list of them), defaults to ``None``.
    :type password: Union[str, bytes, Iterable[Union[str, bytes]]], optional
    :param limit: Return only the first bytes: only the part of the archive that holds them is fetched, and the CRC cannot be checked,
        defaults to ``None``.
    :type limit: int, optional
    :param repo_type: Type of the repository, defaults to ``'dataset'``.
    :type repo_type: RepoTypeTyping, optional
    :param revision: Revision of the repository, defaults to ``'main'``.
    :type revision: str, optional
    :param encoding: Encoding of the names that are not Unicode (``shift_jis``, ``gbk``, ``ibm866``, ...), defaults to ``None`` (guessed).
    :type encoding: str, optional
    :param lang: Hint for guessing that encoding (``'ru'``, ``'ja'``, ...), defaults to ``'en'``.
    :type lang: str, optional
    :param proxies: Proxies for the requests, defaults to ``None``.
    :type proxies: Dict, optional
    :param user_agent: User agent of the requests, defaults to ``None``.
    :type user_agent: Union[Dict, str], optional
    :param headers: Extra headers for the requests, defaults to ``None``.
    :type headers: Dict[str, str], optional
    :param endpoint: The endpoint of the Hub, defaults to ``None`` (the default one).
    :type endpoint: str, optional
    :param hf_token: Access token, defaults to ``None`` (``$HF_TOKEN``).
    :type hf_token: str, optional
    :return: The number of bytes written.
    :rtype: int
    :raises hfutils.index.zip.errors.ZipArchiveNotFound: If the archive does not exist in the repository.
    :raises hfutils.index.zip.errors.NotAZipError: If it is not a zip (``err.detected`` says what it looks like:
        ``'git-lfs-pointer'``, ``'html'``, ``'tar'``, ...).
    :raises hfutils.index.zip.errors.ZipVolumeError: If a volume of a split archive is missing from the repository.
    :raises hfutils.index.zip.errors.ZipFetchError: If the bytes cannot be fetched (``err.status`` is the HTTP status when there was one).
    :raises FileNotFoundError: If there is no such member.
    :raises hfutils.index.zip.errors.ZipPasswordRequiredError: If the member is encrypted and there is no password.
    :raises hfutils.index.zip.errors.ZipPasswordError: If no password opens it.
    :raises hfutils.index.zip.errors.ZipUnsupportedError: If the method or the encryption is not supported.
    :raises hfutils.index.zip.errors.ZipFormatError: If the data is damaged (size or CRC do not match).

    Example::

        >>> import io
        >>> from hfutils.index import hf_zip_file_write_bytes
        >>> buffer = io.BytesIO()
        >>> hf_zip_file_write_bytes('owner/repo', 'archive.zip', 'hello.txt', buffer)
        27
    """
    archive = _open(repo_id, archive_in_repo, password, encoding, lang, repo_type, revision, hf_token, endpoint, proxies,
                    user_agent, headers)
    return write_member(archive, file_in_archive, bin_file, password, limit)


def hf_zip_file_download(repo_id: str, archive_in_repo: str, file_in_archive: str, local_file: str,
                         password: PasswordTyping = None, repo_type: RepoTypeTyping = 'dataset', revision: str = 'main',
                         encoding: Optional[str] = None, lang: str = 'en', proxies: Optional[Dict] = None,
                         user_agent: Union[Dict, str, None] = None, headers: Optional[Dict[str, str]] = None,
                         endpoint: Optional[str] = None, hf_token: Optional[str] = None) -> None:
    """
    Extract a member to a local file.

    The member is written to a temporary file next to ``local_file`` and moved into place when it is complete, so a failed check leaves
    nothing behind.

    :param repo_id: The repository, e.g. ``owner/name``.
    :type repo_id: str
    :param archive_in_repo: The path of the archive in the repository, or of one of its volumes.
    :type archive_in_repo: str
    :param file_in_archive: The path of the member in the archive.
    :type file_in_archive: str
    :param local_file: The file to write; its directory is created.
    :type local_file: str
    :param password: Passwords to try (a ``str``, ``bytes`` or a list of them), defaults to ``None``.
    :type password: Union[str, bytes, Iterable[Union[str, bytes]]], optional
    :param repo_type: Type of the repository, defaults to ``'dataset'``.
    :type repo_type: RepoTypeTyping, optional
    :param revision: Revision of the repository, defaults to ``'main'``.
    :type revision: str, optional
    :param encoding: Encoding of the names that are not Unicode (``shift_jis``, ``gbk``, ``ibm866``, ...), defaults to ``None`` (guessed).
    :type encoding: str, optional
    :param lang: Hint for guessing that encoding (``'ru'``, ``'ja'``, ...), defaults to ``'en'``.
    :type lang: str, optional
    :param proxies: Proxies for the requests, defaults to ``None``.
    :type proxies: Dict, optional
    :param user_agent: User agent of the requests, defaults to ``None``.
    :type user_agent: Union[Dict, str], optional
    :param headers: Extra headers for the requests, defaults to ``None``.
    :type headers: Dict[str, str], optional
    :param endpoint: The endpoint of the Hub, defaults to ``None`` (the default one).
    :type endpoint: str, optional
    :param hf_token: Access token, defaults to ``None`` (``$HF_TOKEN``).
    :type hf_token: str, optional
    :return: ``None``.
    :rtype: None
    :raises hfutils.index.zip.errors.ZipArchiveNotFound: If the archive does not exist in the repository.
    :raises hfutils.index.zip.errors.NotAZipError: If it is not a zip (``err.detected`` says what it looks like:
        ``'git-lfs-pointer'``, ``'html'``, ``'tar'``, ...).
    :raises hfutils.index.zip.errors.ZipVolumeError: If a volume of a split archive is missing from the repository.
    :raises hfutils.index.zip.errors.ZipFetchError: If the bytes cannot be fetched (``err.status`` is the HTTP status when there was one).
    :raises FileNotFoundError: If there is no such member.
    :raises hfutils.index.zip.errors.ZipPasswordRequiredError: If the member is encrypted and there is no password.
    :raises hfutils.index.zip.errors.ZipPasswordError: If no password opens it.
    :raises hfutils.index.zip.errors.ZipUnsupportedError: If the method or the encryption is not supported.
    :raises hfutils.index.zip.errors.ZipFormatError: If the data is damaged (size or CRC do not match).

    Example::

        >>> from hfutils.index import hf_zip_file_download
        >>> hf_zip_file_download('owner/repo', 'archive.zip', 'docs/readme.md', 'out/readme.md')
        >>> open('out/readme.md', 'rb').read()
        b'# Fixture\\n\\nNested markdown member.\\n'
    """
    archive = _open(repo_id, archive_in_repo, password, encoding, lang, repo_type, revision, hf_token, endpoint, proxies,
                    user_agent, headers)
    download_member(archive, file_in_archive, local_file, password)


def hf_zip_cache_reset(maxsize: Optional[int] = None):
    """
    Forget the directories read so far.

    :param maxsize: The new size of the cache, defaults to ``None`` (unchanged).
    :type maxsize: int, optional
    :return: ``None``.
    :rtype: None

    Example::

        >>> from hfutils.index import hf_zip_cache_reset
        >>> hf_zip_cache_reset()
    """
    global _cache
    _cache = LRUCache(maxsize=maxsize or _cache.maxsize)

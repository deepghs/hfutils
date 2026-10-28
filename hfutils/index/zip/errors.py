"""
The errors of the zip readers of :mod:`hfutils.index`.

Every error is a :class:`ZipIndexError` and carries a ``kind`` so that a caller can tell what to do about it:

* ``'fetch'``: the bytes could not be fetched (the transport failed, the archive does not exist), see ``status``;
* ``'format'``: the data is not a zip, or it is damaged, truncated or incomplete (a volume is missing);
* ``'password'``: a member is encrypted and there is no password, or the password is not the right one;
* ``'unsupported'``: a valid zip that uses something that is not implemented (a compression method, strong encryption).

Example::

    >>> from hfutils.index import zip_file_read, ZipIndexError
    >>> try:
    ...     zip_file_read('locked.zip', 'hello.txt')
    ... except ZipIndexError as err:
    ...     print(err.kind, type(err).__name__)
    password ZipPasswordRequiredError
"""
from typing import List, Optional


class ZipIndexError(Exception):
    """
    Base class of the errors of the zip readers.

    :param message: What went wrong, for a person.
    :type message: str
    :param status: The HTTP status when the error comes from a request, defaults to ``None``.
    :type status: int, optional
    :param method: The compression method number when the error is about one, defaults to ``None``.
    :type method: int, optional

    :cvar kind: One of ``'fetch'``, ``'format'``, ``'password'`` and ``'unsupported'``.
    :vartype kind: str
    :ivar status: The HTTP status, if there was one.
    :vartype status: Optional[int]
    :ivar method: The compression method number, if the error is about one.
    :vartype method: Optional[int]

    Example::

        >>> from hfutils.index import ZipIndexError
        >>> err = ZipIndexError('something went wrong', status=500)
        >>> err.kind, err.status, str(err)
        ('format', 500, 'something went wrong')
    """
    kind = 'format'

    def __init__(self, message: str, *, status: Optional[int] = None, method: Optional[int] = None):
        """
        Build the error.

        :param message: What went wrong, for a person.
        :type message: str
        :param status: The HTTP status, defaults to ``None``.
        :type status: int, optional
        :param method: The compression method number, defaults to ``None``.
        :type method: int, optional
        :return: ``None``.
        :rtype: None
        """
        super().__init__(message)
        self.status = status
        self.method = method


class ZipFetchError(ZipIndexError):
    """
    The bytes of the archive could not be fetched (``kind`` is ``'fetch'``).

    Example::

        >>> from hfutils.index import ZipFetchError
        >>> err = ZipFetchError('connection reset', status=503)
        >>> err.kind, err.status
        ('fetch', 503)
    """
    kind = 'fetch'


class ZipArchiveNotFound(ZipFetchError, FileNotFoundError):
    """
    The archive itself does not exist. A missing *volume* of a split archive is a :class:`ZipVolumeError` instead.

    It is a :class:`FileNotFoundError` too, so the usual ``except FileNotFoundError`` works for a local file and a remote one alike.

    :param message: What was looked for, for a person.
    :type message: str

    Example::

        >>> from hfutils.index import zip_list_files, ZipArchiveNotFound
        >>> try:
        ...     zip_list_files('missing.zip')
        ... except ZipArchiveNotFound as err:
        ...     print(err.status, isinstance(err, FileNotFoundError))
        404 True
    """

    def __init__(self, message: str):
        """
        Build the error (its ``status`` is always 404).

        :param message: What was looked for, for a person.
        :type message: str
        :return: ``None``.
        :rtype: None
        """
        super().__init__(message, status=404)


class ZipFormatError(ZipIndexError):
    """
    The archive is damaged, truncated or incomplete (``kind`` is ``'format'``).

    Example::

        >>> from hfutils.index import ZipFormatError
        >>> ZipFormatError('the CRC does not match').kind
        'format'
    """
    kind = 'format'


class NotAZipError(ZipFormatError, ValueError):
    """
    The file is not a zip archive: it has no end of central directory record, whether it is named ``.zip`` or not.

    It is a :class:`ValueError` too.

    :param message: What was found, for a person.
    :type message: str
    :param detected: What the file looks like when it is recognized (``'tar'``, ``'gzip'``, ``'html'``, ``'git-lfs-pointer'``,
        ``'empty'``, ``'truncated-zip'``, ...), defaults to ``None``.
    :type detected: str, optional

    :ivar detected: What the file looks like, ``None`` when nothing is recognized.
    :vartype detected: Optional[str]

    Example::

        >>> from hfutils.index import zip_list_files, NotAZipError
        >>> try:
        ...     zip_list_files('notes.txt')
        ... except NotAZipError as err:
        ...     print(err.detected, err)
        None notes.txt is not a zip archive: no zip end-of-directory record was found.
    """

    def __init__(self, message: str, detected: Optional[str] = None):
        """
        Build the error.

        :param message: What was found, for a person.
        :type message: str
        :param detected: What the file looks like, defaults to ``None``.
        :type detected: str, optional
        :return: ``None``.
        :rtype: None
        """
        super().__init__(message)
        self.detected = detected


class ZipVolumeError(ZipFormatError):
    """
    A volume of a split archive is missing.

    :param message: What is missing, for a person.
    :type message: str
    :param missing: The paths of the volumes that were looked for and not found, defaults to ``None``.
    :type missing: List[str], optional

    :ivar missing: The paths of the volumes that were looked for and not found.
    :vartype missing: List[str]

    Example::

        >>> from hfutils.index import zip_list_files, ZipVolumeError
        >>> try:
        ...     zip_list_files('gap.zip.003')
        ... except ZipVolumeError as err:
        ...     print(err.missing)
        ['gap.zip.002']
    """

    def __init__(self, message: str, missing: Optional[List[str]] = None):
        """
        Build the error.

        :param message: What is missing, for a person.
        :type message: str
        :param missing: The paths of the missing volumes, defaults to ``None``.
        :type missing: List[str], optional
        :return: ``None``.
        :rtype: None
        """
        super().__init__(message)
        self.missing = list(missing or [])


class ZipPasswordRequiredError(ZipIndexError):
    """
    A member is encrypted and no password was given (``kind`` is ``'password'``).

    Example::

        >>> from hfutils.index import zip_file_read, ZipPasswordRequiredError
        >>> try:
        ...     zip_file_read('locked.zip', 'hello.txt')
        ... except ZipPasswordRequiredError as err:
        ...     print(err)
        hello.txt is encrypted: a password is needed.
    """
    kind = 'password'


class ZipPasswordError(ZipIndexError):
    """
    None of the passwords opens the member (``kind`` is ``'password'``).

    ZipCrypto checks a password with one byte, so one wrong password in 256 passes the check; the CRC of the member then refuses it and
    the error says so: the data may be damaged instead.

    Example::

        >>> from hfutils.index import zip_file_read, ZipPasswordError
        >>> try:
        ...     zip_file_read('locked.zip', 'hello.txt', password='wrong')
        ... except ZipPasswordError as err:
        ...     print(err)
        hello.txt: wrong password.
    """
    kind = 'password'


class ZipUnsupportedError(ZipIndexError):
    """
    A valid archive that uses something that is not implemented (``kind`` is ``'unsupported'``): the PPMd, JPEG and WavPack methods,
    PKWARE strong encryption, an encrypted central directory, or a method that needs an optional package that is not installed.

    Example::

        >>> from hfutils.index import zip_file_read, ZipUnsupportedError
        >>> try:
        ...     zip_file_read('ppmd.zip', 'data/table.csv')
        ... except ZipUnsupportedError as err:
        ...     print(err.method)
        98
    """
    kind = 'unsupported'

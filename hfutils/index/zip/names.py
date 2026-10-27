"""
The names of the members of a zip archive: which encoding they are in, and the path they make.

A name is Unicode when the archive says so (the EFS flag, or an Info-ZIP Unicode Path extra field whose CRC matches). Any other
name is a sequence of bytes in whatever code page the tool that wrote it used: Windows writes the OEM code page of the machine
(GBK, Shift-JIS, CP866, ...), the zip default is CP437. :func:`guess_filename_encoding` picks one for the whole archive and the
caller can override it.

The module contains:

* :func:`guess_filename_encoding` - pick the code page of the non-Unicode names of an archive
* :func:`unicode_path_extra`, :func:`is_unicode_name`, :func:`decode_name` - decode one name
* :func:`normalize_segments`, :func:`member_path` - the path a name makes

Example::

    >>> from hfutils.index.zip.names import guess_filename_encoding, member_path
    >>> guess_filename_encoding(['テスト資料.txt'.encode('cp932')])
    'shift_jis'
    >>> member_path('../docs//./readme.md')
    'docs/readme.md'
"""
import re
import struct
import zlib
from typing import Iterable, List, Optional

#: The labels of the encodings that can be asked for (the Python codec behind each one is in ``_CODECS``).
FILENAME_ENCODINGS = ('utf-8', 'shift_jis', 'gbk', 'big5', 'euc-kr', 'cp437', 'ibm866', 'koi8-r', 'windows-1251', 'windows-1252')

# The WHATWG encodings of those labels are supersets of the Python codecs of the same name (windows-31j, gb18030, big5-hkscs,
# windows-949), which is what real archives need: Python's strict ``shift_jis`` refuses NEC / IBM extensions such as the circled digits.
_CODECS = {
    'utf-8': 'utf-8', 'shift_jis': 'cp932', 'gbk': 'gb18030', 'big5': 'big5hkscs', 'euc-kr': 'cp949',
    'cp437': 'cp437', 'ibm866': 'cp866', 'koi8-r': 'koi8_r', 'windows-1251': 'cp1251', 'windows-1252': 'cp1252',
}
_CJK = ('shift_jis', 'gbk', 'big5', 'euc-kr')
# Windows' own zip writer uses the OEM code page of the machine.
_OEM_CODE_PAGE = {'ru': 'ibm866', 'uk': 'ibm866', 'be': 'ibm866', 'ja': 'shift_jis', 'zh': 'gbk', 'zh-tw': 'big5', 'zh-hk': 'big5',
                  'ko': 'euc-kr'}
_KANA = re.compile('[ぁ-ヿ]')
_UTF8_FLAG = 0x800
_common_characters = None


def _codec(encoding: str) -> str:
    try:
        return _CODECS[encoding]
    except KeyError:
        raise ValueError(f'Unknown filename encoding {encoding!r}, one of {FILENAME_ENCODINGS!r} expected.') from None


def _strict_decode(encoding: str, raw: bytes) -> Optional[str]:
    try:
        return raw.decode(_codec(encoding))
    except UnicodeDecodeError:
        return None


def _block(encoding: str, lead_from: int, lead_to: int, trail_from: int, trail_to: int) -> frozenset:
    raw = bytes(b for a in range(lead_from, lead_to + 1) for b in (a, *range(trail_from, trail_to + 1)))
    # one pair at a time: a lead byte followed by every trail byte would decode wrongly when a trail byte is a lead byte
    chars = set()
    for a in range(lead_from, lead_to + 1):
        for b in range(trail_from, trail_to + 1):
            try:
                chars.update(bytes((a, b)).decode(_codec(encoding)))
            except UnicodeDecodeError:
                pass
    del raw
    return frozenset(chars)


def _common_character_sets() -> dict:
    """The frequently used characters of each CJK code page, from its "level 1" byte block (no table is shipped)."""
    global _common_characters
    if _common_characters is None:
        _common_characters = {
            'shift_jis': _block('shift_jis', 0x88, 0x98, 0x40, 0xfc),  # JIS X 0208 level 1 kanji
            'gbk': _block('gbk', 0xb0, 0xd7, 0xa1, 0xfe),  # GB 2312 level 1 hanzi
            'big5': _block('big5', 0xa4, 0xc6, 0x40, 0xfe),  # Big5 frequently used hanzi
            'euc-kr': _block('euc-kr', 0xb0, 0xc8, 0xa1, 0xfe),  # KS X 1001 hangul
        }
    return _common_characters


def guess_filename_encoding(raw_names: Iterable[bytes], lang: str = 'en') -> str:
    """
    Guess one encoding for the non-Unicode names of an archive.

    UTF-8 when every name is valid UTF-8, else the CJK code page whose decoding is made of common characters, else the OEM code page of
    ``lang``, else CP437 (the zip default). The single byte code pages cannot be told apart reliably, hence the locale step and the
    ``encoding`` argument of the public functions. Korean text in CP949 also decodes to common characters in GBK: ask for it with
    ``encoding='euc-kr'``.

    :param raw_names: The names as bytes, as they are in the archive.
    :type raw_names: Iterable[bytes]
    :param lang: The language of the reader (``'ru'``, ``'ja'``, ``'zh-tw'``, ...), defaults to ``'en'``.
    :type lang: str, optional
    :return: One of :data:`FILENAME_ENCODINGS`.
    :rtype: str

    Example::

        >>> from hfutils.index.zip.names import guess_filename_encoding
        >>> guess_filename_encoding([b'plain.txt'])
        'utf-8'
        >>> guess_filename_encoding(['测试资料.txt'.encode('gbk')])
        'gbk'
        >>> guess_filename_encoding(['Привет'.encode('cp866')], lang='ru')
        'ibm866'
        >>> guess_filename_encoding(['Привет'.encode('cp866')])
        'cp437'
    """
    names = [raw for raw in raw_names if any(b >= 0x80 for b in raw)]
    if all(_strict_decode('utf-8', raw) is not None for raw in names):
        return 'utf-8'
    common = _common_character_sets()
    best = None
    for encoding in _CJK:
        decoded = [_strict_decode(encoding, raw) for raw in names]
        if any(d is None for d in decoded):
            continue
        good = total = 0
        for ch in ''.join(decoded):
            if ord(ch) < 0x80:
                continue
            total += 1
            if ch in common[encoding] or (encoding == 'shift_jis' and _KANA.match(ch)):
                good += 1
        score = good / total if total else 0.0
        if best is None or score > best[1]:
            best = (encoding, score)
    if best and best[1] >= 0.9:
        return best[0]
    locale = lang.lower()
    oem = _OEM_CODE_PAGE.get(locale) or _OEM_CODE_PAGE.get(locale.split('-')[0])
    if oem and all(_strict_decode(oem, raw) is not None for raw in names):
        return oem
    return 'cp437'


def unicode_path_extra(extra: bytes, raw_name: bytes) -> Optional[str]:
    """
    The name of an Info-ZIP Unicode Path extra field (0x7075), when its CRC says it belongs to this ``raw_name``.

    :param extra: The extra field data of a record.
    :type extra: bytes
    :param raw_name: The name of the record as it is stored.
    :type raw_name: bytes
    :return: The Unicode name, or ``None`` when there is no such field or it belongs to another name.
    :rtype: Optional[str]

    Example::

        >>> import struct, zlib
        >>> from hfutils.index.zip.names import unicode_path_extra
        >>> raw = b'\\x82\\xa0.txt'
        >>> body = struct.pack('<BI', 1, zlib.crc32(raw)) + 'あ.txt'.encode('utf-8')
        >>> extra = struct.pack('<HH', 0x7075, len(body)) + body
        >>> unicode_path_extra(extra, raw)
        'あ.txt'
        >>> unicode_path_extra(extra, b'other.txt') is None
        True
    """
    pos = 0
    while pos + 4 <= len(extra):
        tag, size = struct.unpack_from('<HH', extra, pos)
        body = extra[pos + 4:pos + 4 + size]
        if tag == 0x7075 and len(body) >= 5 and body[0] == 1:
            if struct.unpack_from('<I', body, 1)[0] == zlib.crc32(raw_name) & 0xffffffff:
                return body[5:].decode('utf-8', 'replace')
        pos += 4 + size
    return None


def is_unicode_name(flags: int, unicode_extra: Optional[str]) -> bool:
    """
    Tell whether the name of a record can be trusted to be Unicode.

    Only the EFS flag and a verified Unicode Path field make a name trustworthy: legacy bytes are sometimes valid UTF-8 too.

    :param flags: The general purpose flags of the record.
    :type flags: int
    :param unicode_extra: What :func:`unicode_path_extra` returned for the record.
    :type unicode_extra: Optional[str]
    :return: ``True`` when the name is Unicode.
    :rtype: bool

    Example::

        >>> from hfutils.index.zip.names import is_unicode_name
        >>> is_unicode_name(0x800, None), is_unicode_name(0, 'name'), is_unicode_name(0, None)
        (True, True, False)
    """
    return bool(flags & _UTF8_FLAG) or unicode_extra is not None


def decode_name(raw_name: bytes, flags: int, unicode_extra: Optional[str], encoding: str) -> str:
    """
    Decode the name of a record: as Unicode when the archive says so, else with ``encoding``.

    :param raw_name: The name as it is stored.
    :type raw_name: bytes
    :param flags: The general purpose flags of the record.
    :type flags: int
    :param unicode_extra: What :func:`unicode_path_extra` returned for the record.
    :type unicode_extra: Optional[str]
    :param encoding: The encoding of names that are not Unicode, one of :data:`FILENAME_ENCODINGS`.
    :type encoding: str
    :return: The name.
    :rtype: str
    :raises ValueError: If ``encoding`` is not one of :data:`FILENAME_ENCODINGS`.

    Example::

        >>> from hfutils.index.zip.names import decode_name
        >>> decode_name(b'caf\\xe9.txt', 0, None, 'windows-1252')
        'café.txt'
        >>> decode_name('café.txt'.encode('utf-8'), 0x800, None, 'cp437')
        'café.txt'
    """
    if unicode_extra is not None:
        return unicode_extra
    if flags & _UTF8_FLAG:
        return raw_name.decode('utf-8', 'replace')
    return raw_name.decode(_codec(encoding), 'replace')


def normalize_segments(path: str) -> List[str]:
    """
    Split a path into segments without empty ones, ``.`` and ``..``: nothing a name does can leave the root of the archive.

    :param path: A path with ``/`` as the separator.
    :type path: str
    :return: The segments.
    :rtype: List[str]

    Example::

        >>> from hfutils.index.zip.names import normalize_segments
        >>> normalize_segments('/a/./b//../c/')
        ['a', 'b', 'c']
    """
    return [s for s in (part.strip() for part in path.split('/')) if s and s not in ('.', '..')]


def member_path(name: str) -> Optional[str]:
    """
    The path a member is listed under.

    Names that are not files give ``None``: directories (also those written without the directory flag), and names that are nothing
    after the normalization. A name with no ``/`` is read with a backslash as the separator, as some Windows tools write it.

    :param name: The decoded name of a record.
    :type name: str
    :return: The normalized path, or ``None``.
    :rtype: Optional[str]

    Example::

        >>> from hfutils.index.zip.names import member_path
        >>> member_path('../docs//./readme.md')
        'docs/readme.md'
        >>> member_path('win\\\\dir\\\\a.txt')
        'win/dir/a.txt'
        >>> member_path('docs/') is None
        True
    """
    if '/' not in name:
        name = name.replace('\\', '/')
    if name.endswith('/'):
        return None
    return '/'.join(normalize_segments(name)) or None

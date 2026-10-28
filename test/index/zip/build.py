"""A small zip writer for the tests that need an archive the standard library never writes: damaged records, saturated 32-bit fields
with ZIP64 extra fields, volumes with wrong numbers, members with lying sizes. It stores (method 0) unless told otherwise."""
import struct
import zlib
from typing import List, Optional, Tuple

from hfutils.index.zip.crypto import ZipCryptoKeys


def zipcrypto_encrypt(password: bytes, plain: bytes, check: int) -> bytes:
    """The 12-byte header and the data of a traditional-encryption member (the random part of the header is fixed)."""
    keys = ZipCryptoKeys(password)
    out = bytearray()
    for p in bytes(11) + bytes([check]) + plain:
        t = (keys.k2 | 2) & 0xffff
        out.append(p ^ (((t * (t ^ 1)) >> 8) & 0xff))
        keys.update(p)
    return bytes(out)


def parts(entries: List[dict], prefix: bytes = b'') -> Tuple[bytes, bytes]:
    """``(local part, central directory)``. Every entry is a dict: ``name`` (str or bytes) and ``data`` (the stored bytes) plus
    optional overrides: ``method``, ``flags``, ``crc``, ``csize`` / ``usize`` (the central directory and the local header),
    ``extra`` (central) / ``local_extra``, ``disk``, ``cd_lho`` (the offset the directory claims), ``time``."""
    body = bytearray(prefix)
    cd = bytearray()
    for e in entries:
        raw = e['name'].encode('utf-8') if isinstance(e['name'], str) else e['name']
        data = e.get('data', b'')
        crc = e.get('crc', zlib.crc32(data) & 0xffffffff)
        csize, usize = e.get('csize', len(data)), e.get('usize', len(data))
        flags, method, time = e.get('flags', 0), e.get('method', 0), e.get('time', 0)
        lextra, cextra = e.get('local_extra', b''), e.get('extra', b'')
        lho = len(body) - len(prefix)
        body += struct.pack('<4sHHHHHIIIHH', b'PK\x03\x04', 20, flags, method, time, 0x21, crc, csize, usize, len(raw),
                            len(lextra)) + raw + lextra + data
        cd += struct.pack('<4sHHHHHHIIIHHHHHII', b'PK\x01\x02', 20, 20, flags, method, time, 0x21, crc, csize, usize, len(raw),
                          len(cextra), 0, e.get('disk', 0), 0, 0, e.get('cd_lho', lho)) + raw + cextra
    return bytes(body), bytes(cd)


def eocd(cd_size: int, cd_offset: int, n: int, this_disk: int = 0, cd_disk: int = 0, comment: bytes = b'',
         n_here: Optional[int] = None) -> bytes:
    return struct.pack('<4sHHHHIIH', b'PK\x05\x06', this_disk, cd_disk, n if n_here is None else n_here, n, cd_size, cd_offset,
                       len(comment)) + comment


def zip_bytes(entries: List[dict], comment: bytes = b'', prefix: bytes = b'') -> bytes:
    body, cd = parts(entries, prefix)
    return body + cd + eocd(len(cd), len(body) - len(prefix), len(entries), comment=comment)


def zip64_records(n: int, cd_size: int, cd_offset: int, at: int, extensible: bytes = b'') -> bytes:
    """The ZIP64 end record and its locator; ``at`` is the offset the record will have."""
    record = struct.pack('<4sQHHIIQQQQ', b'PK\x06\x06', 44 + len(extensible), 45, 45, 0, 0, n, n, cd_size, cd_offset) + extensible
    return record + struct.pack('<4sIQI', b'PK\x06\x07', 0, at, 1)


def zip64_extra(size=None, csize=None, lho=None, disk=None) -> bytes:
    """A ZIP64 extra field with the given fields in the order the specification fixes."""
    body = b''.join(struct.pack('<Q', v) for v in (size, csize, lho) if v is not None)
    if disk is not None:
        body += struct.pack('<I', disk)
    return struct.pack('<HH', 1, len(body)) + body

"""
A throw-away dataset repository with zip archives in it, for the tests of the remote zip functions and of ``hfutils ils``.

It is built from ``test/testfile/zipfiles`` (whose bytes are fixed, so the recording is reproducible) plus a few things that are not
zips, and uploaded with one commit. Paths in the repository:

* ``zips/<fixture name>`` the single-file archives;  ``odd/archive.jar`` and ``odd/noext`` are copies under other names;
* ``split/...`` the two split sets, ``gap/...`` a 7-Zip set that lacks its middle volume;
* ``notzip/...`` a tar, a Git LFS pointer, an HTML page, an empty file, a PNG header;
* ``big/stored.zip`` a stored 768 KiB member, to read in several windows.
"""
import hashlib
import io
import zipfile

import pytest
from huggingface_hub import CommitOperationAdd

from test.testings import get_testfile

SINGLE = ['methods-bzip2.zip', 'methods-lzma.zip', 'methods-deflate64.zip', 'methods-zstd.zip', 'methods-ppmd.zip',
          'crypto-zipcrypto.zip', 'crypto-aes256.zip', 'crypto-two-passwords.zip', 'names-shiftjis.zip', 'names-gbk.zip',
          'names-odd.zip', 'prefix-sfx.zip', 'zip64-missing-records.zip', 'empty.zip', 'thirdparty-ziprs-implode.zip',
          'thirdparty-libarchive-unicode-path.zip', 'thirdparty-libarchive-xz.zipx']
SPLIT = {'split/split-7z.zip.001': 'split-7z.zip.001', 'split/split-7z.zip.002': 'split-7z.zip.002',
         'split/split-7z.zip.003': 'split-7z.zip.003', 'split/split-infozip.z01': 'split-infozip.z01',
         'split/split-infozip.z02': 'split-infozip.z02', 'split/split-infozip.zip': 'split-infozip.zip',
         'gap/split-7z.zip.001': 'split-7z.zip.001', 'gap/split-7z.zip.003': 'split-7z.zip.003'}
BIG_MEMBER = 'payload.bin'
LFS_POINTER = (b'version https://git-lfs.github.com/spec/v1\n'
               b'oid sha256:' + b'ab' * 32 + b'\nsize 12345\n')


def big_payload() -> bytes:
    """768 KiB that do not compress, the same on every run."""
    out, i = b'', 0
    while len(out) < 768 * 1024:
        out += hashlib.sha256(b'zip-big-%d' % i).digest()
        i += 1
    return out[:768 * 1024]


def big_archive() -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, 'w', zipfile.ZIP_STORED) as zf:
        zf.writestr(zipfile.ZipInfo(BIG_MEMBER, date_time=(2024, 1, 2, 3, 4, 6)), big_payload())
    return buf.getvalue()


def operations():
    ops = [CommitOperationAdd(f'zips/{name}', get_testfile('zipfiles', name)) for name in SINGLE]
    ops += [CommitOperationAdd(dst, get_testfile('zipfiles', src)) for dst, src in SPLIT.items()]
    ops += [CommitOperationAdd('odd/archive.jar', get_testfile('zipfiles', 'methods-bzip2.zip')),
            CommitOperationAdd('odd/noext', get_testfile('zipfiles', 'methods-bzip2.zip')),
            CommitOperationAdd('notzip/real.tar', get_testfile('raw.tar')),
            CommitOperationAdd('notzip/pointer.zip', LFS_POINTER),
            CommitOperationAdd('notzip/page.zip', b'<!DOCTYPE html><html><body>Not Found</body></html>'),
            CommitOperationAdd('notzip/empty.zip', b''),
            CommitOperationAdd('notzip/image.zip', b'\x89PNG\r\n\x1a\n' + b'\x00' * 200),
            CommitOperationAdd('big/stored.zip', big_archive())]
    return ops


@pytest.fixture()
def zip_repo(hf_repo, hf_client, hf_vcr):
    with hf_vcr.segment('files'):
        hf_client.create_commit(hf_repo, operations(), repo_type='dataset', commit_message='zip fixtures')
    yield hf_repo

import copy
import os.path
from functools import partial
from typing import Literal

from .base import register_archive_type
from .zip import _ZLIB_SUPPORTED
from ..utils import walk_files, tqdm

try:
    import bz2

    del bz2
    _BZ2_SUPPORTED = True
except ImportError:
    _BZ2_SUPPORTED = False

try:
    import lzma

    del lzma
    _LZMA_SUPPORTED = True
except ImportError:
    _LZMA_SUPPORTED = False

try:
    from pwd import getpwnam
except ImportError:
    getpwnam = None

try:
    from grp import getgrnam
except ImportError:
    getgrnam = None

CompressTyping = Literal['', 'gzip', 'bzip2', 'xz']


def _get_gid(name):
    if getgrnam is None or name is None:
        return None
    try:
        result = getgrnam(name)
    except KeyError:
        result = None
    if result is not None:
        return result[2]
    return None


def _get_uid(name):
    if getpwnam is None or name is None:
        return None
    try:
        result = getpwnam(name)
    except KeyError:
        result = None
    if result is not None:
        return result[2]
    return None


def _tarfile_pack(directory, tar_file, compress: CompressTyping = "gzip",
                  owner=None, group=None, silent: bool = False):
    if compress is None:
        tar_compression = ''
    elif compress == 'gzip':
        tar_compression = 'gz'
    elif compress == 'bzip2':
        tar_compression = 'bz2'
    elif compress == 'xz':
        tar_compression = 'xz'
    else:
        raise ValueError("bad value for 'compress', or compression format not "
                         "supported : {0}".format(compress))

    import tarfile  # late import for breaking circular dependency

    uid = _get_uid(owner)
    gid = _get_gid(group)

    def _set_uid_gid(tarinfo):
        if gid is not None:
            tarinfo.gid = gid
            tarinfo.gname = group
        if uid is not None:
            tarinfo.uid = uid
            tarinfo.uname = owner
        return tarinfo

    with tarfile.open(tar_file, f'w|{tar_compression}') as tar:
        progress = tqdm(walk_files(directory), silent=silent, desc=f'Packing {directory!r} ...')
        for file in progress:
            progress.set_description(file)
            tar.add(os.path.join(directory, file), file, filter=_set_uid_gid)


def _tarfile_unpack(tar_file, directory, silent: bool = False, numeric_owner=False):
    import tarfile  # late import for breaking circular dependency

    with tarfile.open(tar_file) as tar:
        directories = []
        for tarinfo in tar:
            if tarinfo.isdir():
                # Extract directories with a safe mode.
                directories.append(tarinfo)
                tarinfo = copy.copy(tarinfo)
                tarinfo.mode = 0o700
            # Do not set_attrs directories, as we will do that further down
            tar.extract(tarinfo, directory, set_attrs=not tarinfo.isdir(),
                        numeric_owner=numeric_owner)

        # Reverse sort directories.
        directories.sort(key=lambda a: a.name)
        directories.reverse()

        # Set correct owner, mtime and filemode on directories.
        for tarinfo in directories:
            dirpath = os.path.join(directory, tarinfo.name)
            tar.chown(tarinfo, dirpath, numeric_owner=numeric_owner)
            tar.utime(tarinfo, dirpath)
            tar.chmod(tarinfo, dirpath)


register_archive_type('tar', ['.tar'], partial(_tarfile_pack, compress=None), _tarfile_unpack)
if _ZLIB_SUPPORTED:
    register_archive_type('gztar', ['.tar.gz', '.tgz'], partial(_tarfile_pack, compress='gzip'), _tarfile_unpack)
if _BZ2_SUPPORTED:
    register_archive_type('bztar', ['.tar.bz2', '.tbz2'], partial(_tarfile_pack, compress='bzip2'), _tarfile_unpack)
if _LZMA_SUPPORTED:
    register_archive_type('xztar', ['.tar.xz', '.txz'], partial(_tarfile_pack, compress='xz'), _tarfile_unpack)

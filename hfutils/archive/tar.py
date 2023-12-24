import copy
import os.path
import tarfile
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

CompressTyping = Literal['', 'gzip', 'bzip2', 'xz']


def _tarfile_pack(directory, tar_file, compress: CompressTyping = "gzip", silent: bool = False):
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

    with tarfile.open(tar_file, f'w|{tar_compression}') as tar:
        progress = tqdm(walk_files(directory), silent=silent, desc=f'Packing {directory!r} ...')
        for file in progress:
            progress.set_description(file)
            tar.add(os.path.join(directory, file), file)


def _tarfile_unpack(tar_file, directory, silent: bool = False, numeric_owner=False):
    with tarfile.open(tar_file) as tar:
        directories = []
        progress = tqdm(tar, silent=silent, desc=f'Unpacking {directory!r} ...')
        for tarinfo in progress:
            progress.set_description(tarinfo.name)
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
        progress = tqdm(directories, silent=silent, desc=f'Applying directories ...')
        for tarinfo in progress:
            progress.set_description(tarinfo.name)
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

"""
Overview:
    Archive pack and unpack management.

Supported Formats:

    .. include:: supported_types.demo.py.txt

.. note::
    If you require support for 7z and RAR formats, simply install ``hfutils`` using the following code:

    .. code:: shell

        pip install hfutils[7z]
        pip install hfutils[rar]

.. warning::
    The creation of archive files in the RAR format is not supported, as we utilize the `rarfile <https://github.com/markokr/rarfile>`_ library, which does not offer functionality for creating RAR files.
"""
from .base import register_archive_type, archive_pack, archive_unpack, get_archive_type, get_archive_extname, \
    archive_writer, ArchiveWriter, archive_splitext
from .rar import _rar_pack, _rar_unpack, RARWriter
from .sevenz import _7z_pack, _7z_unpack, SevenZWriter
from .tar import _tarfile_pack, _tarfile_unpack, TarWriter
from .zip import _zip_pack, _zip_unpack, ZipWriter

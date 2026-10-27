"""
Overview:
    Random access to the members of a zip archive, on the local disk (``zip_*``) or in a Hugging Face repository (``hf_zip_*``).

    The zip's own central directory is the index, so there is no index file to make or to keep fresh. The modules:

    * :mod:`.local` and :mod:`.fetch`: the public functions;
    * :mod:`.directory`: the end record, ZIP64, the central directory, volumes, and telling a zip from what is not one;
    * :mod:`.reader`: reading a member (fetch, decrypt, decompress, check) and the password policy;
    * :mod:`.codecs`, :mod:`.legacy`, :mod:`.crypto`: the compression methods and the two encryptions;
    * :mod:`.source`: where the bytes come from (a file, volumes, Range requests); :mod:`.names`: encodings of names;
    * :mod:`.errors`: the exceptions, each with a ``kind``.

    Example::

        >>> from hfutils.index import zip_list_files, zip_file_read
        >>> zip_list_files('archive.zip')
        ['hello.txt', 'data/table.csv', 'docs/readme.md', 'images/noise.jpg']
        >>> zip_file_read('archive.zip', 'hello.txt', limit=5)
        b'hello'
"""
from .errors import ZipIndexError, ZipFetchError, ZipArchiveNotFound, ZipFormatError, NotAZipError, ZipVolumeError, \
    ZipPasswordRequiredError, ZipPasswordError, ZipUnsupportedError
from .fetch import hf_zip_get_index, hf_zip_list_files, hf_zip_file_exists, hf_zip_file_info, hf_zip_file_size, \
    hf_zip_file_read, hf_zip_file_write_bytes, hf_zip_file_download, hf_zip_cache_reset
from .local import zip_get_index, zip_list_files, zip_file_exists, zip_file_info, zip_file_size, zip_file_read, \
    zip_file_write_bytes, zip_file_download, zip_cache_reset

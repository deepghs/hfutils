"""
This module provides functionality for identifying archive and compressed files based on their filenames.

It includes a comprehensive list of known archive and compressed file extensions, as well as patterns for
identifying split archives and other generic compressed file formats. The main
function :func:`is_archive_or_compressed` can be used to determine if a given filename
represents an archive or compressed file.

The module is useful for file handling operations where it's necessary to distinguish between regular files
and archives or compressed files.
"""

import os.path
import re
from typing import Union

_ARCHIVE_KNOWN_EXTS = {
    '.tar',  # Tape Archive
    '.rar',  # Roshal Archive
    '.rar5',  # RAR version 5
    '.zip',  # ZIP archive
    '.7z',  # 7-Zip archive
    '.7zip',  # Alternative extension for 7-Zip
    '.gz',  # Gzip compressed file
    '.bz2',  # Bzip2 compressed file
    '.xz',  # XZ compressed file
    '.ace',  # ACE archive
    '.lz',  # Lzip compressed file
    '.lzma',  # LZMA compressed file
    '.z',  # Compress (Unix) file
    '.cab',  # Microsoft Cabinet file
    '.arj',  # ARJ archive
    '.iso',  # ISO disk image
    '.lzh',  # LZH archive
    '.sit',  # StuffIt archive
    '.sitx',  # StuffIt X archive
    '.sea',  # Self-Extracting Archive
    '.alz',  # ALZip archive
    '.egg',  # Python Egg
    '.whl',  # Python Wheel
    '.deb',  # Debian package
    '.rpm',  # Red Hat Package Manager
    '.pkg',  # macOS Installer Package
    '.dmg',  # Apple Disk Image
    '.msi',  # Microsoft Installer
    '.tgz',  # Gzipped tar archive
    '.tbz2',  # Bzip2 compressed tar archive
    '.lzw',  # LZW compressed file
    '.rz',  # RZip compressed file
    '.lzo',  # Lempel-Ziv-Oberhumer compressed file
    '.zst',  # Zstandard compressed file
    '.tar.gz',  # Gzipped tar archive
    '.tar.bz2',  # Bzip2 compressed tar archive
    '.tar.xz',  # XZ compressed tar archive
    '.tar.lz',  # Lzip compressed tar archive
    '.tar.lzma',  # LZMA compressed tar archive
    '.zipx',  # Extended ZIP archive
    '.arc',  # ARC archive
    '.ark',  # ARC archive (alternative extension)
    '.lha',  # LHA archive
    '.zoo',  # ZOO archive
    '.gca',  # GCA archive
    '.uc2',  # UC2 archive
    '.uha',  # UHarc archive
    '.war',  # Web Application Archive
    '.ear',  # Enterprise Application aRchive
    '.sar',  # SAR archive
    '.jar',  # Java Archive
    '.apk',  # Android Package Kit
    '.xpi',  # XPInstall (Mozilla browser extension)
    '.snap',  # Snap package (Ubuntu)
    '.appimage',  # AppImage package
    '.squashfs',  # Squashfs filesystem
    '.cpio',  # CPIO archive
    '.shar',  # Shell archive
    '.lbr',  # LBR archive
    '.mar',  # Mozilla Archive
    '.sbx',  # Sandbox file
    '.qcow2',  # QEMU Copy On Write 2
    '.vdi',  # VirtualBox Disk Image
    '.vhd',  # Virtual Hard Disk
    '.vmdk',  # Virtual Machine Disk
    '.ova',  # Open Virtual Appliance
    '.xar',  # eXtensible ARchive
    '.mpq',  # MoPaQ archive (Blizzard games)
}

# Additional generic patterns
_EXTERNAL_PATTERNS = [
    r'\.tar(?:\.(?:gz|bz2|xz|lz|lzma|Z))?$',  # Tar and compressed tar archives
    r'\.t\.(?:gz|bz2|xz|lz|lzma|Z)$',  # Compressed files with .t.XX extension
    r'\.(?:zip|z)$',  # ZIP archives and Z compressed files
    r'\.rar$',  # RAR archives
    r'\.7z$',  # 7-Zip archives
    r'\.(?:ar|a)$',  # AR archives
    r'\.(?:lz|lzma?)$',  # LZ and LZMA compressed files
    r'\.gz(?:ip)?$',  # Gzip compressed files
    r'\.bz(?:ip)?2?$',  # Bzip and Bzip2 compressed files
    r'\.(?:xz|lzh|lha)$',  # XZ, LZH, and LHA archives
    r'\.(?:iso|img|dmg|pkg|msi)$',  # Disk images and installers
    r'\.(?:deb|rpm|apk|ipa)$',  # Package formats
]

_ARCHIVE_SPLIT_PATTERNS = [
    r'^(.+\.(?:zip|rar|7z|tar|tar\.gz|tar\.bz2|tar\.xz))\.\d+$',  # Split archives (e.g., .zip.001)
    r'^(.+\.t)\.[a-z0-9]{2,4}$',  # Split archives with .t.XX extension
    r'^(.+\.part\d+)\.rar$',  # Split RAR archives
    r'^(.+)\.r\d{2}$',  # Old-style split RAR archives
]


def is_archive_or_compressed(filename: Union[str, os.PathLike]) -> bool:
    """
    Determine if the given filename represents an archive or compressed file.

    This function checks the filename against a list of known archive and compressed file extensions,
    as well as patterns for split archives and other generic compressed file formats.

    :param filename: The name of the file to check. Can be a string or a path-like object.
    :type filename: Union[str, os.PathLike]

    :return: True if the filename represents an archive or compressed file, False otherwise.
    :rtype: bool

    :raises TypeError: If the filename is not a string or path-like object.

    Usage:
        >>> is_archive_or_compressed('example.zip')
        True
        >>> is_archive_or_compressed('document.txt')
        False
        >>> is_archive_or_compressed('archive.tar.gz')
        True
        >>> is_archive_or_compressed('split_archive.zip.001')
        True
    """
    if not isinstance(filename, (str, os.PathLike)):
        raise TypeError(f'Unknown file name type - {filename!r}')
    filename = os.path.basename(os.path.normcase(str(filename)))

    # Check for known extensions
    for ext in _ARCHIVE_KNOWN_EXTS:
        if filename.lower().endswith(ext):
            return True

    # Check for split archives
    for pattern in _ARCHIVE_SPLIT_PATTERNS:
        match = re.match(pattern, filename.lower())
        if match:
            return True

    # Check for external patterns
    for pattern in _EXTERNAL_PATTERNS:
        if re.search(pattern, filename.lower()):
            return True

    return False

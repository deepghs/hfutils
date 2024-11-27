"""
This module provides utilities for handling file extensions, particularly for files with composite extensions.
It extends the standard os.path.splitext functionality to support multi-part file extensions.
"""

import os


def splitext_with_composite(filename, composite_extensions):
    """
    Split a filename into a pair (root, ext) where ext is a composite extension if it matches
    one of the provided composite extensions, otherwise behaves like os.path.splitext.

    This function is particularly useful when dealing with files that have multi-part extensions
    (e.g., '.tar.gz', '.config.json') where standard os.path.splitext would only split at the
    last dot.

    :param filename: The filename to split.
    :type filename: str
    :param composite_extensions: A sequence of composite extensions to check against (e.g., ['.tar.gz', '.config.json']).
                               The matching is case-insensitive.
    :type composite_extensions: list[str] or tuple[str]

    :return: A tuple containing the root and the extension. If the filename ends with any of the
            composite extensions, the extension will be the full composite extension. Otherwise,
            returns the result of os.path.splitext.
    :rtype: tuple[str, str]

    :example:
        >>> splitext_with_composite('file.tar.gz', ['.tar.gz'])
        ('file', '.tar.gz')
        >>> splitext_with_composite('file.config.json', ['.config.json'])
        ('file', '.config.json')
        >>> splitext_with_composite('file.txt', ['.tar.gz'])
        ('file', '.txt')
    """
    for ext in composite_extensions:
        if filename.lower().endswith(ext.lower()):
            return filename[:-len(ext)], filename[-len(ext):]
    return os.path.splitext(filename)

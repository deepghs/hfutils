"""
This module provides utilities for file handling, specifically for walking through directories
and retrieving file paths. It includes a function to recursively search for files in a specified
directory based on a given pattern.

The primary function is `walk_files`, which allows users to easily obtain relative paths of all
files within a directory structure, making it useful for file management tasks, data processing,
and more.
"""
import glob
import os
from typing import Iterator, Optional


def walk_files(directory: str, pattern: Optional[str] = None, ) -> Iterator[str]:
    """
    Recursively walk through a directory and yield relative paths of all files.

    This function takes a directory path and a pattern to search for files. It uses the `glob`
    module to find all files that match the specified pattern within the directory and its
    subdirectories. The yielded paths are relative to the specified directory.

    :param directory: The root directory to start walking.
    :type directory: str
    :param pattern: The pattern to match files against, defaults to ``**/*`` which matches all files.
    :type pattern: str

    :return: An iterator that yields relative paths of all files in the directory.
    :rtype: Iterator[str]

    :example:

    >>> for file in walk_files('/path/to/directory'):
    ...     print(file)
    """
    for path in glob.glob(os.path.abspath(os.path.join(directory, pattern or os.path.join('**', '*'))), recursive=True):
        if os.path.isfile(path):
            yield os.path.relpath(path, start=os.path.abspath(directory))

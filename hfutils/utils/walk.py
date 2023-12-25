import os
from typing import Iterator


def walk_files(directory: str) -> Iterator[str]:
    """
    Recursively walk through a directory and yield relative paths of all files.

    :param directory: The root directory to start walking.
    :type directory: str

    :return: An iterator that yields relative paths of all files in the directory.
    :rtype: Iterator[str]
    """
    for root, dirs, files in os.walk(directory):
        for file in files:
            path = os.path.abspath(os.path.join(root, file))
            yield os.path.relpath(path, start=directory)

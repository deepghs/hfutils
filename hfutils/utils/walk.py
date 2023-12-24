import os
from typing import Iterator


def walk_files(directory: str) -> Iterator[str]:
    for root, dirs, files in os.walk(directory):
        for file in files:
            path = os.path.abspath(os.path.join(root, file))
            yield os.path.relpath(path, start=directory)

"""
A module for managing and grouping files based on size and structure.

This module provides functionality for walking through directories, grouping files based on
various criteria, and managing file collections with size constraints. It's particularly
useful for tasks involving file organization, batch processing, and storage management.

Example usage:
    >>> groups = walk_files_with_groups("./data", pattern="*.txt", max_total_size="1GB")
    >>> for group in groups:
    ...     print(f"Group size: {group.size}, File count: {group.count}")
"""

import os
import pathlib
from collections import defaultdict
from dataclasses import dataclass
from typing import List, Union, Optional

from hbutils.scale import size_to_bytes
from natsort import natsorted
from tqdm import tqdm

from .heap import Heap
from .walk import walk_files


@dataclass
class FileItem:
    """
    A data class representing a single file with its properties.

    :param file: Path to the file
    :type file: str
    :param size: Size of the file in bytes
    :type size: int
    :param count: Number of files this item represents (typically 1)
    :type count: int
    """

    file: str
    size: int
    count: int

    @classmethod
    def from_file(cls, file: str, rel_to: Optional[str] = None) -> 'FileItem':
        """
        Create a FileItem instance from a file path.

        :param file: Path to the file
        :type file: str
        :param rel_to: Optional path to make the file path relative to
        :type rel_to: Optional[str]

        :return: A new FileItem instance
        :rtype: FileItem
        :raises FileNotFoundError: If the file does not exist
        """
        file = pathlib.Path(file).resolve(strict=True)
        size = os.path.getsize(str(file))
        if rel_to:
            rel_to = pathlib.Path(rel_to).resolve(strict=True)
            file = file.relative_to(rel_to)

        return cls(
            file=str(file),
            size=size,
            count=1,
        )


@dataclass
class FilesGroup:
    """
    A data class representing a group of files with collective properties.

    :param files: List of file paths in the group
    :type files: List[str]
    :param size: Total size of all files in the group
    :type size: int
    :param count: Total number of files in the group
    :type count: int
    """

    files: List[str]
    size: int
    count: int

    @classmethod
    def new(cls) -> 'FilesGroup':
        """
        Create a new empty FilesGroup instance.

        :return: A new empty FilesGroup
        :rtype: FilesGroup
        """
        return cls(
            files=[],
            size=0,
            count=0,
        )

    def add(self, file: Union[FileItem, 'FilesGroup']) -> 'FilesGroup':
        """
        Add a FileItem or another FilesGroup to this group.

        :param file: The item to add to the group
        :type file: Union[FileItem, FilesGroup]

        :return: Self reference for method chaining
        :rtype: FilesGroup
        :raises TypeError: If the input type is not FileItem or FilesGroup
        """
        if isinstance(file, FileItem):
            self.files.append(file.file)
            self.size += file.size
            self.count += file.count
        elif isinstance(file, FilesGroup):
            self.files.extend(file.files)
            self.size += file.size
            self.count += file.count
        else:
            raise TypeError(f'Unknown type {type(file)!r} to add - {file!r}.')

        return self


def _group_by_default(files: List[FileItem]) -> List[Union[FileItem, FilesGroup]]:
    """
    Default grouping function that returns files as-is.

    :param files: List of FileItem objects
    :type files: List[FileItem]

    :return: The same list of FileItems
    :rtype: List[Union[FileItem, FilesGroup]]
    """
    return files


def _group_by_segs(files: List[FileItem], segs: int) -> List[Union[FileItem, FilesGroup]]:
    """
    Group files by their path segments.

    :param files: List of FileItem objects
    :type files: List[FileItem]
    :param segs: Number of path segments to use for grouping
    :type segs: int

    :return: List of grouped files
    :rtype: List[Union[FileItem, FilesGroup]]
    """
    d = defaultdict(FilesGroup.new)
    for file in files:
        d[pathlib.Path(file.file).parts[:segs]].add(file)

    retval = []
    for key, value in natsorted(d.items()):
        retval.append(value)
    return retval


def _group_by(files: List[FileItem], group_method: Optional[Union[str, int]] = None) \
        -> List[Union[FileItem, FilesGroup]]:
    """
    Group files according to the specified method.

    :param files: List of FileItem objects to group
    :type files: List[FileItem]
    :param group_method: Method for grouping (None for default, int for segment count)
    :type group_method: Optional[Union[str, int]]

    :return: List of grouped files
    :rtype: List[Union[FileItem, FilesGroup]]
    :raises TypeError: If group_method is of an unsupported type
    :raises ValueError: If group_method is invalid or unsupported
    """
    if isinstance(group_method, int):
        pass  # is an int
    elif isinstance(group_method, str):
        try:
            group_method = int(group_method)
        except (TypeError, ValueError):
            pass  # is a str
    elif isinstance(group_method, type(None)):
        pass  # default policy
    else:
        raise TypeError(f'Unknown group by method - {group_method!r}.')

    if isinstance(group_method, int) and group_method == 0:
        raise ValueError('Unable to group by 0 segments.')

    if group_method is None:
        return _group_by_default(files)
    elif isinstance(group_method, int):
        return _group_by_segs(files, segs=group_method)
    else:
        raise ValueError(f'Unsupported group by method - {group_method!r}.')


def walk_files_with_groups(directory: str, pattern: Optional[str] = None,
                           group_method: Optional[Union[str, int]] = None,
                           max_total_size: Optional[Union[str, float]] = None,
                           silent: bool = False) \
        -> List[FilesGroup]:
    """
    Walk through a directory and group files based on specified criteria.

    This function walks through a directory, collecting files that match the given pattern,
    and groups them according to the specified method while respecting size constraints.

    :param directory: Root directory to start walking from
    :type directory: str
    :param pattern: Optional glob pattern to filter files
    :type pattern: Optional[str]
    :param group_method: Method for grouping files (None for default, int for segment count)
    :type group_method: Optional[Union[str, int]]
    :param max_total_size: Maximum total size for each group (can be string like "1GB")
    :type max_total_size: Optional[Union[str, float]]
    :param silent: If True, the progress bar content will not be displayed.
    :type silent: bool

    :return: List of file groups
    :rtype: List[FilesGroup]
    :raises ValueError: If the grouping parameters are invalid
    :raises OSError: If there are filesystem-related errors

    Example:
        >>> groups = walk_files_with_groups("./data", "*.txt", group_method=2, max_total_size="1GB")
        >>> for group in groups:
        ...     print(f"Group contains {group.count} files, total size: {group.size} bytes")
    """
    all_items = [
        FileItem.from_file(os.path.join(directory, file), rel_to=directory)
        for file in tqdm(walk_files(directory, pattern=pattern), desc=f'Scanning {directory!r} ...', disable=silent)
    ]
    if max_total_size is not None and isinstance(max_total_size, str):
        max_total_size = size_to_bytes(max_total_size)
    if max_total_size is None:
        final_group = FilesGroup.new()
        for file_item in all_items:
            final_group.add(file_item)
        return [final_group]

    else:
        raw_groups: List[Union[FileItem, FilesGroup]] = _group_by(all_items, group_method=group_method)
        collected_groups: List[FilesGroup] = []
        heap: Heap[FilesGroup] = Heap(key=lambda x: (x.size, x.count))
        for group in tqdm(raw_groups, desc='Arranging Files', disable=silent):
            if not heap or (heap.peek().size + group.size) > max_total_size:
                new_group = FilesGroup.new()
                heap.push(new_group)
                collected_groups.append(new_group)
            item = heap.pop()
            item.add(group)
            heap.push(item)

        collected_groups = [item for item in collected_groups if item.count > 0]
        return collected_groups

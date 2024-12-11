"""
This module provides functionality for analyzing and managing Hugging Face repository files.

It includes classes and functions for representing repository files, creating file lists,
and analyzing repository contents. The module is designed to work with the Hugging Face
Hub API and provides utilities for handling file paths, sizes, and other metadata.

Key components:
- RepoFileItem: Represents a single file in a repository.
- RepoFileList: A sequence of RepoFileItems with additional metadata and utility methods.
- hf_hub_repo_analysis: Function to analyze repository contents based on given criteria.

This module is particularly useful for developers working with Hugging Face repositories
and need to analyze or manage file structures and metadata.
"""

import os.path
from collections.abc import Sequence
from dataclasses import dataclass
from operator import itemgetter
from typing import Optional, List, Literal, Tuple

from hbutils.scale import size_to_bytes_str
from hbutils.string import plural_word, format_tree
from huggingface_hub.hf_api import RepoFile

from ..operate import list_all_with_pattern
from ..operate.base import RepoTypeTyping
from ..utils import hf_normpath, hf_fs_path


@dataclass
class RepoFileItem:
    """
    Represents a file item in a Hugging Face repository.

    This class encapsulates metadata about a single file, including its path,
    size, LFS status, and blob ID.

    :param path: The file path relative to the repository root.
    :param size: The size of the file in bytes.
    :param is_lfs: Whether the file is stored using Git LFS.
    :param lfs_sha256: The SHA256 hash of the LFS file, if applicable.
    :param blob_id: The Git blob ID of the file.
    """

    path: str
    size: int
    is_lfs: bool
    lfs_sha256: Optional[str]
    blob_id: str

    @classmethod
    def from_repo_file(cls, repo_file: RepoFile, subdir: str = '') -> 'RepoFileItem':
        """
        Create a RepoFileItem from a RepoFile object.

        :param repo_file: The RepoFile object to convert.
        :param subdir: The subdirectory to use as the base path (default: '').
        :return: A new RepoFileItem instance.
        """
        subdir = subdir or '.'
        return cls(
            path=hf_normpath(os.path.relpath(repo_file.path, subdir)),
            size=repo_file.lfs.size if repo_file.lfs else repo_file.size,
            is_lfs=bool(repo_file.lfs),
            lfs_sha256=repo_file.lfs.sha256 if repo_file.lfs else None,
            blob_id=repo_file.blob_id,
        )

    @property
    def path_segments(self) -> Tuple[str, ...]:
        """
        Get the path segments of the file.

        :return: A tuple of path segments.
        """
        return tuple(seg for seg in self.path.split('/') if seg and seg != '.')

    def __repr__(self):
        """
        Return a string representation of the RepoFileItem.

        :return: A formatted string representation.
        """
        return (f'<{self.__class__.__name__} {self.path}, size: {size_to_bytes_str(self.size, sigfigs=3, system="si")}'
                f'{" (LFS)" if self.is_lfs else ""}>')


class RepoFileList(Sequence):
    """
    Represents a list of RepoFileItems with additional metadata and utility methods.

    This class provides a way to manage and analyze a collection of files from a
    Hugging Face repository, including information about the repository itself.

    :param repo_id: The ID of the repository.
    :param items: A list of RepoFileItem objects.
    :param repo_type: The type of the repository (default: 'dataset').
    :param revision: The revision of the repository (default: 'main').
    :param subdir: The subdirectory within the repository (default: '').
    """

    def __init__(self, repo_id: str, items: List[RepoFileItem],
                 repo_type: RepoTypeTyping = 'dataset', revision: str = 'main', subdir: Optional[str] = ''):
        self.repo_id = repo_id
        self.repo_type = repo_type
        self.revision = revision
        self.subdir = hf_normpath(subdir or '.')
        self._file_items = list(items)
        self._total_size = 0
        for item in self._file_items:
            self._total_size += item.size

    def __getitem__(self, index):
        """
        Get a RepoFileItem by index.

        :param index: The index of the item to retrieve.
        :return: The RepoFileItem at the specified index.
        """
        return self._file_items[index]

    def __len__(self) -> int:
        """
        Get the number of items in the list.

        :return: The number of RepoFileItems in the list.
        """
        return len(self._file_items)

    @property
    def total_size(self) -> int:
        """
        Get the total size of all files in the list.

        :return: The total size in bytes.
        """
        return self._total_size

    def _tree(self, max_items: Optional[int] = 10):
        """
        Generate a tree representation of the file list.

        :param max_items: The maximum number of items to include in the tree (default: 10).
        :return: A tuple containing the tree title and list of tree nodes.
        """
        title = hf_fs_path(
            repo_id=self.repo_id,
            repo_type=self.repo_type,
            revision=self.revision,
            filename=self.subdir,
        )
        return (
            f'{title} ({plural_word(len(self._file_items), "file")}, '
            f'{size_to_bytes_str(self._total_size, sigfigs=3, system="si")})',
            [
                *(
                    (repr(item), []) for item in
                    (self._file_items[:max_items] if max_items and max_items > 0 else self._file_items)
                ),
                *(
                    [
                        (f'... ({plural_word(len(self._file_items), "file")}) in total ...', [])
                    ] if max_items and 0 < max_items < len(self._file_items) else []
                )
            ]
        )

    def __repr__(self):
        """
        Return a string representation of the RepoFileList.

        :return: A formatted string representation of the file list.
        """
        return format_tree(
            self._tree(),
            format_node=itemgetter(0),
            get_children=itemgetter(1),
        )

    def repr(self, max_items: Optional[int] = 10):
        """
        Generate a custom string representation of the RepoFileList.

        :param max_items: The maximum number of items to include in the representation (default: 10).
        :return: A formatted string representation of the file list.
        """
        return format_tree(
            self._tree(max_items=max_items),
            format_node=itemgetter(0),
            get_children=itemgetter(1),
        )


SortByTyping = Literal['none', 'path', 'size']


def hf_hub_repo_analysis(
        repo_id: str, pattern: str = '**/*', repo_type: RepoTypeTyping = 'dataset',
        revision: str = 'main', hf_token: Optional[str] = None, silent: bool = False,
        subdir: str = '', sort_by: SortByTyping = 'path', **kwargs,
) -> RepoFileList:
    """
    Analyze the contents of a Hugging Face repository.

    This function retrieves file information from a specified repository and creates
    a RepoFileList object containing detailed information about each file.

    :param repo_id: The ID of the repository to analyze.
    :param pattern: A glob pattern to filter files (default: '**/*').
    :param repo_type: The type of the repository (default: 'dataset').
    :param revision: The revision of the repository to analyze (default: 'main').
    :param hf_token: The Hugging Face API token (optional).
    :param silent: Whether to suppress output (default: False).
    :param subdir: The subdirectory within the repository to analyze (default: '').
    :param sort_by: How to sort the file list ('none', 'path', or 'size') (default: 'path').
    :param kwargs: Additional keyword arguments to pass to list_all_with_pattern.

    :return: A RepoFileList object containing the analysis results.

    :raises: May raise exceptions related to API access or file operations.

    Usage:
        >>> result = hf_hub_repo_analysis('username/repo', pattern='*.txt', repo_type='model')
        >>> print(result)
    """
    if subdir and subdir != '.':
        pattern = f'{subdir}/{pattern}'

    file_items = []
    for item in list_all_with_pattern(
            repo_id=repo_id,
            repo_type=repo_type,
            revision=revision,
            pattern=pattern,
            hf_token=hf_token,
            silent=silent,
            **kwargs
    ):
        if isinstance(item, RepoFile):
            file_items.append(RepoFileItem.from_repo_file(item, subdir))

    if sort_by != 'none':
        file_items = sorted(file_items,
                            key=lambda x: x.path_segments if sort_by == 'path' else (-x.size, x.path_segments))

    return RepoFileList(
        repo_id=repo_id,
        repo_type=repo_type,
        revision=revision,
        subdir=subdir,
        items=file_items
    )

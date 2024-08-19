"""
This module provides functionality for listing and displaying files from a HuggingFace repository in a tree-like structure.

It includes functions for parsing repository paths, retrieving file information, and formatting the output as a tree.
The module also defines a CLI command for easy interaction with the tree functionality.

Key components:

- TreeItem: A dataclass representing an item (file or folder) in the tree structure.
- _get_tree: Function to retrieve the tree structure of files in a HuggingFace repository.
- _add_tree_subcommand: Function to add the 'tree' subcommand to a Click CLI group.

Usage:
This module is typically used as part of a larger CLI application for interacting with HuggingFace repositories.
The 'tree' command can be used to visualize the structure of files in a repository.
"""

import dataclasses
import os
import re
from typing import Optional, List, Union

import click
from hbutils.string import format_tree
from huggingface_hub import configure_http_backend
from huggingface_hub.hf_api import RepoFile
from natsort import natsorted

from .base import CONTEXT_SETTINGS
from ..operate.base import REPO_TYPES, list_files_in_repository, RepoTypeTyping, get_hf_client
from ..utils import get_requests_session, hf_normpath, get_file_type, hf_fs_path, FileItemType


@dataclasses.dataclass
class TreeItem:
    """
    Represents an item (file or folder) in the tree structure.

    :param name: The name of the item.
    :type name: str
    :param type_: The type of the item (file or folder).
    :type type_: FileItemType
    :param children: List of child items if this is a folder.
    :type children: Optional[List[TreeItem]]
    :param exist: Whether the item exists in the repository.
    :type exist: bool

    :ivar name: The name of the item.
    :ivar type_: The type of the item.
    :ivar children: List of child items.
    :ivar exist: Existence status of the item.
    """

    name: str
    type_: FileItemType
    children: Optional[List['TreeItem']]
    exist: bool = True

    def get_name(self):
        """
        Get the formatted name of the item for display.

        :return: Formatted name string with color and strike-through if applicable.
        :rtype: str
        """
        return click.style(
            self.name,
            fg=self.type_.render_color if self.exist else None,
            strikethrough=not self.exist,
        ) + ('' if self.exist else ' <NOT EXIST>')

    def get_children(self):
        """
        Get the children of this item if it's a folder.

        :return: List of child items if folder, empty list otherwise.
        :rtype: List[TreeItem]
        """
        return self.children if self.type_ == FileItemType.FOLDER else []


def _get_tree(repo_id: str, repo_type: RepoTypeTyping, dir_in_repo: str,
              revision: Optional[str] = None, show_all: bool = False) -> TreeItem:
    """
    Retrieve the tree structure of files in a HuggingFace repository.

    :param repo_id: The ID of the repository.
    :type repo_id: str
    :param repo_type: The type of the repository.
    :type repo_type: RepoTypeTyping
    :param dir_in_repo: The directory in the repository to start from.
    :type dir_in_repo: str
    :param revision: The revision of the repository to use.
    :type revision: Optional[str]
    :param show_all: Whether to show hidden files.
    :type show_all: bool

    :return: The root TreeItem representing the directory structure.
    :rtype: TreeItem
    """
    root = {}
    for filepath in list_files_in_repository(
            repo_id=repo_id,
            repo_type=repo_type,
            subdir=dir_in_repo,
            revision=revision,
            ignore_patterns=[],
    ):
        filename = hf_normpath(os.path.relpath(filepath, dir_in_repo))
        segments = re.split(r'[\\/]+', filename)
        if any(segment.startswith('.') and segment != '.' for segment in segments) and not show_all:
            continue

        current_node = root
        for i, segment in enumerate(segments):
            if segment not in current_node:
                if i == (len(segments) - 1):
                    current_node[segment] = get_file_type(segment)
                else:
                    current_node[segment] = {}
            current_node = current_node[segment]

    root_name = hf_fs_path(
        repo_id=repo_id,
        repo_type=repo_type,
        filename=dir_in_repo,
        revision=revision,
    )

    def _recursion(cur_node: Union[dict, FileItemType], parent_name: str, is_exist: bool = False):
        if isinstance(cur_node, dict):
            return TreeItem(
                name=parent_name,
                type_=FileItemType.FOLDER,
                children=[
                    _recursion(cur_node=value, parent_name=name, is_exist=is_exist)
                    for name, value in natsorted(cur_node.items())
                ],
                exist=is_exist,
            )
        else:
            return TreeItem(
                name=parent_name,
                type_=cur_node,
                children=[],
                exist=is_exist,
            )

    exist = True
    if not root:
        hf_client = get_hf_client()
        paths = hf_client.get_paths_info(
            repo_id=repo_id,
            repo_type=repo_type,
            revision=revision,
            paths=[dir_in_repo],
        )
        if len(paths) == 0:
            exist = False
        elif len(paths) == 1:
            pathobj = paths[0]
            if isinstance(pathobj, RepoFile):  # the subdir is a file
                root = get_file_type(dir_in_repo)
        else:
            assert len(paths) == 1, \
                f'Multiple path {dir_in_repo!r} found in repo {root_name!r}, ' \
                f'this must be caused by HuggingFace API.'  # pragma: no cover

    return _recursion(
        cur_node=root,
        parent_name=root_name,
        is_exist=exist,
    )


def _add_tree_subcommand(cli: click.Group) -> click.Group:
    """
    Add the 'tree' subcommand to a Click CLI group.

    This function defines a new 'tree' command that lists files from a HuggingFace repository
    in a tree-like structure.

    :param cli: The Click CLI group to add the command to.
    :type cli: click.Group

    :return: The modified CLI group with the 'tree' command added.
    :rtype: click.Group

    Usage:
        This function is typically called when setting up a CLI application:

        cli = click.Group()
        cli = _add_tree_subcommand(cli)
    """

    @cli.command('tree', help='List files as a tree from HuggingFace repository.\n\n'
                              'Set environment $HF_TOKEN to use your own access token.',
                 context_settings=CONTEXT_SETTINGS)
    @click.option('-r', '--repository', 'repo_id', type=str, required=True,
                  help='Repository to download from.')
    @click.option('-t', '--type', 'repo_type', type=click.Choice(REPO_TYPES), default='dataset',
                  help='Type of the HuggingFace repository.', show_default=True)
    @click.option('-d', '--directory', 'dir_in_repo', type=str, default=None,
                  help='Directory in repository to download the full directory tree.')
    @click.option('-R', '--revision', 'revision', type=str, default='main',
                  help='Revision of repository.', show_default=True)
    @click.option('-a', '--all', 'show_all', is_flag=True, type=bool, default=False,
                  help='Show all files, including hidden files.', show_default=True)
    def tree(repo_id: str, repo_type: RepoTypeTyping, dir_in_repo, revision: str, show_all: bool):
        """
        List files as a tree from a HuggingFace repository in a tree-like structure.

        :param repo_id: The ID of the repository.
        :type repo_id: str
        :param repo_type: The type of the repository.
        :type repo_type: RepoTypeTyping
        :param dir_in_repo: The directory in the repository to start from.
        :type dir_in_repo: str
        :param revision: The revision of the repository to use.
        :type revision: str
        :param show_all: Whether to show hidden files.
        :type show_all: bool
        """
        configure_http_backend(get_requests_session)

        _tree = _get_tree(
            repo_id=repo_id,
            repo_type=repo_type,
            dir_in_repo=dir_in_repo or '.',
            revision=revision,
            show_all=show_all,
        )
        print(format_tree(
            _tree,
            format_node=TreeItem.get_name,
            get_children=TreeItem.get_children,
        ))

    return cli

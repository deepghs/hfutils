import dataclasses
import os
import re
from typing import Optional, List, Union

import click
from hbutils.string import format_tree
from huggingface_hub import configure_http_backend
from natsort import natsorted

from .base import CONTEXT_SETTINGS
from ..operate.base import REPO_TYPES, list_files_in_repository, RepoTypeTyping
from ..utils import get_requests_session, hf_normpath, get_file_type, hf_fs_path, FileItemType


@dataclasses.dataclass
class _TreeItem:
    name: str
    type_: FileItemType
    children: Optional[List['_TreeItem']]

    def get_name(self):
        return click.style(self.name, fg=self.type_.render_color)

    def get_children(self):
        return self.children if self.type_ == FileItemType.FOLDER else []


def _get_tree(repo_id: str, repo_type: RepoTypeTyping, dir_in_repo: str,
              revision: Optional[str] = None, show_all: bool = False) -> _TreeItem:
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
        if any(segment.startswith('.') for segment in segments) and not show_all:
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

    def _recursion(cur_node: Union[dict, FileItemType], parent_name: str):
        if isinstance(cur_node, dict):
            return _TreeItem(
                name=parent_name,
                type_=FileItemType.FOLDER,
                children=[
                    _recursion(cur_node=value, parent_name=name)
                    for name, value in natsorted(cur_node.items())
                ]
            )
        else:
            return _TreeItem(
                name=parent_name,
                type_=cur_node,
                children=[],
            )

    return _recursion(
        cur_node=root,
        parent_name=root_name,
    )


def _add_tree_subcommand(cli: click.Group) -> click.Group:
    @cli.command('tree', help='List files from HuggingFace repository.\n\n'
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
            format_node=_TreeItem.get_name,
            get_children=_TreeItem.get_children,
        ))

    return cli

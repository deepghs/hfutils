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
class _TreeItem:
    name: str
    type_: FileItemType
    children: Optional[List['_TreeItem']]
    exist: bool = True

    def get_name(self):
        return click.style(
            self.name,
            fg=self.type_.render_color if self.exist else None,
            strikethrough=not self.exist,
        )

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
            return _TreeItem(
                name=parent_name,
                type_=FileItemType.FOLDER,
                children=[
                    _recursion(cur_node=value, parent_name=name, is_exist=is_exist)
                    for name, value in natsorted(cur_node.items())
                ],
                exist=is_exist,
            )
        else:
            return _TreeItem(
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

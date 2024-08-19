import os.path
import os.path
from typing import Union, List

import click
import tzlocal
from huggingface_hub import configure_http_backend
from huggingface_hub.hf_api import RepoFolder, RepoFile

from .base import CONTEXT_SETTINGS
from ..operate.base import REPO_TYPES, get_hf_client
from ..utils import get_requests_session, FileItemType, get_file_type


class ListItem:
    """
    Class representing a list item.

    :param item: The item object.
    :type item: Union[RepoFolder, RepoFile]
    :param base_dir: The base directory.
    :type base_dir: str
    """

    def __init__(self, item: Union[RepoFolder, RepoFile], base_dir: str):
        self.item = item
        self.base_dir = base_dir
        if isinstance(item, RepoFolder):
            self.type = FileItemType.FOLDER
        else:
            self.type = get_file_type(item.path)


def _add_ls_subcommand(cli: click.Group) -> click.Group:
    """
    Add the 'ls' subcommand to the CLI.

    :param cli: The Click CLI application.
    :type cli: click.Group
    :return: The modified Click CLI application.
    :rtype: click.Group
    """

    @cli.command('ls', help='List files from HuggingFace repository.\n\n'
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
    @click.option('-l', '--list', 'show_detailed', is_flag=True, type=bool, default=False,
                  help='Show detailed file information.', show_default=True)
    def ls(repo_id: str, repo_type: str, dir_in_repo, revision: str, show_all: bool, show_detailed: bool):
        """
        List files from a HuggingFace repository.

        :param repo_id: The identifier of the repository.
        :type repo_id: str
        :param repo_type: The type of the HuggingFace repository.
        :type repo_type: str
        :param dir_in_repo: The directory in the repository to list files from.
        :type dir_in_repo: str
        :param revision: The revision of the repository.
        :type revision: str
        :param show_all: Flag to indicate whether to show all files, including hidden files.
        :type show_all: bool
        :param show_detailed: Flag to indicate whether to show detailed file information.
        :type show_detailed: bool
        """
        configure_http_backend(get_requests_session)

        hf_client = get_hf_client()
        items: List[ListItem] = []
        for item in hf_client.list_repo_tree(
                repo_id=repo_id,
                repo_type=repo_type,
                path_in_repo=dir_in_repo,
                revision=revision,
                recursive=False,
                expand=show_detailed,
        ):
            relpath = os.path.relpath(item.path, dir_in_repo)
            if not show_all and relpath.startswith('.'):
                continue

            item = ListItem(item, dir_in_repo)
            items.append(item)
            if not show_detailed:
                print(click.style(
                    os.path.relpath(item.item.path, item.base_dir),
                    fg=item.type.render_color
                ))

        if show_detailed:
            max_size_length = 0
            max_commit_info_length = 0
            for item in items:
                if item.type == FileItemType.FOLDER:
                    size_text = '-'
                else:
                    size_text = str(item.item.size)
                max_size_length = max(max_size_length, len(size_text))

                commit_text = (item.item.last_commit.title or '').splitlines(keepends=False)[0]
                max_commit_info_length = max(max_commit_info_length, len(commit_text))

            for item in items:
                print('d' if item.type == FileItemType.FOLDER else '-', end='')
                print('L' if item.type != FileItemType.FOLDER and item.item.lfs else '-', end='')

                commit_text = (item.item.last_commit.title or '').splitlines(keepends=False)[0]
                print(
                    ' ' + ' ' * (max_commit_info_length - len(commit_text)) +
                    click.style(commit_text, underline=True),
                    end=''
                )

                if item.type == FileItemType.FOLDER:
                    size_text = '-'
                else:
                    size_text = str(item.item.size)
                size_text = ' ' * (max_size_length - len(size_text)) + size_text
                print(' ' + size_text, end='')

                print(' ' + item.item.last_commit.oid[:8], end='')
                commit_time = item.item.last_commit.date.astimezone(tzlocal.get_localzone())
                print(' ' + commit_time.strftime('%Y-%m-%d %H:%M %Z'), end='')

                print(' ' + click.style(
                    os.path.relpath(item.item.path, item.base_dir),
                    fg=item.type.render_color
                ))

    return cli

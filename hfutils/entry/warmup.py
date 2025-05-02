"""
This module provides functionality for warming-up data from HuggingFace repositories.

It includes a CLI command for warming-up files, archives, or directories from HuggingFace,
with various options for customization. The module also defines custom exceptions and
utility functions to support the warmup process.

Usage:
    This module is typically used as part of a larger CLI application for
    interacting with HuggingFace repositories.
"""

import warnings
from typing import Optional

import click
from huggingface_hub import configure_http_backend

from .base import CONTEXT_SETTINGS, command_wrap, ClickErrorException
from ..operate import hf_warmup_file, hf_warmup_directory
from ..operate.base import REPO_TYPES, RepoTypeTyping, _IGNORE_PATTERN_UNSET
from ..utils import get_requests_session


class NoRemotePathAssignedWithWarmup(ClickErrorException):
    """
    Custom exception class for indicating that no remote path in the repository is assigned.

    This exception is raised when a warmup is attempted without specifying a file,
    archive, or directory to warmup from the repository.

    :attribute exit_code: The exit code to be used when this exception is raised.
    :type exit_code: int
    """
    exit_code = 0x41


def _add_warmup_subcommand(cli: click.Group) -> click.Group:
    """
    Add the 'warmup' subcommand to the CLI.

    This function defines and adds the 'warmup' command to the given CLI group.
    It sets up all the necessary options and implements the warmup functionality.

    :param cli: The Click CLI application to which the warmup command will be added.
    :type cli: click.Group
    :return: The modified Click CLI application with the warmup command added.
    :rtype: click.Group
    """

    @cli.command('warmup', help='Warmup data from HuggingFace.\n\n'
                                'Set environment $HF_TOKEN to use your own access token.',
                 context_settings=CONTEXT_SETTINGS)
    @click.option('-r', '--repository', 'repo_id', type=str, required=True,
                  help='Repository to warmup from.')
    @click.option('-t', '--type', 'repo_type', type=click.Choice(REPO_TYPES), default='dataset',
                  help='Type of the HuggingFace repository.', show_default=True)
    @click.option('-f', '--filename', 'file_in_repo', type=str, default=None,
                  help='File in repository to warmup.')
    @click.option('-d', '--directory', 'dir_in_repo', type=str, default=None,
                  help='Directory in repository to warmup the full directory tree.')
    @click.option('-R', '--revision', 'revision', type=str, default='main',
                  help='Revision of repository.', show_default=True)
    @click.option('-n', '--max_workers', 'max_workers', type=int, default=8,
                  help='Max threads to warmup.', show_default=True)
    @click.option('-w', '--wildcard', 'wildcard', type=str, default=None,
                  help='Wildcard for files to warmup. Only applied when -d is used.', show_default=True)
    @click.option('--all', 'show_all', is_flag=True, type=bool, default=False,
                  help='Show all files, including hidden files.', show_default=True)
    @command_wrap()
    def warmup(
            repo_id: str, repo_type: RepoTypeTyping,
            file_in_repo: Optional[str], dir_in_repo: Optional[str],
            revision: str, max_workers: int, wildcard: Optional[str],
            show_all: bool = False,
    ):
        """
        Warmup data from HuggingFace repositories.

        This function implements the core functionality of the warmup command.
        It handles warming-up individual files, archives, or entire directories
        from HuggingFace repositories based on the provided options.

        :param repo_id: Repository to warmup from.
        :type repo_id: str
        :param repo_type: Type of the HuggingFace repository.
        :type repo_type: RepoTypeTyping
        :param file_in_repo: File in repository to warmup.
        :type file_in_repo: Optional[str]
        :param dir_in_repo: Directory in repository to warmup the full directory tree.
        :type dir_in_repo: Optional[str]
        :param revision: Revision of repository.
        :type revision: str
        :param max_workers: Max workers to warmup
        :type max_workers: int
        :param wildcard: Wildcard for files to warmup. Only applied when -d is used.
        :type wildcard: Optional[str]
        :param show_all: Show all files, including hidden files.
        :type show_all: bool

        :raises NoRemotePathAssignedWithWarmup: If no remote path in repository is assigned.
        """
        configure_http_backend(get_requests_session)

        if not file_in_repo and not dir_in_repo:
            raise NoRemotePathAssignedWithWarmup('No remote path in repository assigned.\n'
                                                 'One of the -f, or -d option is required.')

        if file_in_repo:
            if dir_in_repo:
                warnings.warn('File in repository assigned, value of -d option will be ignored.')
            hf_warmup_file(
                repo_id=repo_id,
                repo_type=repo_type,
                filename=file_in_repo,
                revision=revision,
            )

        elif dir_in_repo:
            hf_warmup_directory(
                repo_id=repo_id,
                repo_type=repo_type,
                dir_in_repo=dir_in_repo,
                pattern=wildcard or '**/*',
                revision=revision,
                silent=False,
                max_workers=max_workers,
                ignore_patterns=_IGNORE_PATTERN_UNSET if not show_all else [],
            )

        else:
            assert False, 'Should not reach this line, it must be a bug!'  # pragma: no cover

    return cli

"""
This module provides functionality for downloading data from HuggingFace repositories.

It includes a CLI command for downloading files, archives, or directories from HuggingFace,
with various options for customization. The module also defines custom exceptions and
utility functions to support the download process.

Usage:
    This module is typically used as part of a larger CLI application for
    interacting with HuggingFace repositories.
"""

import os
import warnings
from typing import Optional

import click
from huggingface_hub import configure_http_backend

from .base import CONTEXT_SETTINGS, command_wrap, ClickErrorException
from ..operate import download_file_to_file, download_archive_as_directory, download_directory_as_directory
from ..operate.base import REPO_TYPES, RepoTypeTyping, _IGNORE_PATTERN_UNSET
from ..utils import get_requests_session


class NoRemotePathAssignedWithDownload(ClickErrorException):
    """
    Custom exception class for indicating that no remote path in the repository is assigned.

    This exception is raised when a download is attempted without specifying a file,
    archive, or directory to download from the repository.

    :attribute exit_code: The exit code to be used when this exception is raised.
    :type exit_code: int
    """
    exit_code = 0x11


def _add_download_subcommand(cli: click.Group) -> click.Group:
    """
    Add the 'download' subcommand to the CLI.

    This function defines and adds the 'download' command to the given CLI group.
    It sets up all the necessary options and implements the download functionality.

    :param cli: The Click CLI application to which the download command will be added.
    :type cli: click.Group
    :return: The modified Click CLI application with the download command added.
    :rtype: click.Group
    """

    @cli.command('download', help='Download data from HuggingFace.\n\n'
                                  'Set environment $HF_TOKEN to use your own access token.',
                 context_settings=CONTEXT_SETTINGS)
    @click.option('-r', '--repository', 'repo_id', type=str, required=True,
                  help='Repository to download from.')
    @click.option('-t', '--type', 'repo_type', type=click.Choice(REPO_TYPES), default='dataset',
                  help='Type of the HuggingFace repository.', show_default=True)
    @click.option('-f', '--filename', 'file_in_repo', type=str, default=None,
                  help='File in repository to download.')
    @click.option('-a', '--archive', 'archive_in_repo', type=str, default=None,
                  help='Archive file in repository to download and extract from')
    @click.option('-d', '--directory', 'dir_in_repo', type=str, default=None,
                  help='Directory in repository to download the full directory tree.')
    @click.option('-o', '--output', 'output_path', type=str, required=True,
                  help='Output path for download.')
    @click.option('-R', '--revision', 'revision', type=str, default='main',
                  help='Revision of repository.', show_default=True)
    @click.option('-n', '--max_workers', 'max_workers', type=int, default=8,
                  help='Max threads to download.', show_default=True)
    @click.option('-p', '--password', 'password', type=str, default=None,
                  help='Password for the archive file. Only applied when -a is used.', show_default=True)
    @click.option('-w', '--wildcard', 'wildcard', type=str, default=None,
                  help='Wildcard for files to download. Only applied when -d is used.', show_default=True)
    @click.option('-s', '--soft_mode_when_check', 'soft_mode_when_check', is_flag=True, type=bool, default=False,
                  help='Just check the file size when validating the downloaded files.', show_default=True)
    @click.option('--tmpdir', 'tmpdir', type=str, default=None,
                  help='Use custom temporary Directory.', show_default=True)
    @click.option('--all', 'show_all', is_flag=True, type=bool, default=False,
                  help='Show all files, including hidden files.', show_default=True)
    @command_wrap()
    def download(
            repo_id: str, repo_type: RepoTypeTyping,
            file_in_repo: Optional[str], archive_in_repo: Optional[str], dir_in_repo: Optional[str],
            output_path: str, revision: str, max_workers: int,
            password: Optional[str], wildcard: Optional[str], soft_mode_when_check: bool, tmpdir: Optional[str],
            show_all: bool = False,
    ):
        """
        Download data from HuggingFace repositories.

        This function implements the core functionality of the download command.
        It handles downloading individual files, archives, or entire directories
        from HuggingFace repositories based on the provided options.

        :param repo_id: Repository to download from.
        :type repo_id: str
        :param repo_type: Type of the HuggingFace repository.
        :type repo_type: RepoTypeTyping
        :param file_in_repo: File in repository to download.
        :type file_in_repo: Optional[str]
        :param archive_in_repo: Archive file in repository to download and extract from.
        :type archive_in_repo: Optional[str]
        :param dir_in_repo: Directory in repository to download the full directory tree.
        :type dir_in_repo: Optional[str]
        :param output_path: Output path for download.
        :type output_path: str
        :param revision: Revision of repository.
        :type revision: str
        :param max_workers: Max workers to download
        :type max_workers: int
        :param password: Password for the archive file. Only applied when -a is used.
        :type password: Optional[str]
        :param wildcard: Wildcard for files to download. Only applied when -d is used.
        :type wildcard: Optional[str]
        :param soft_mode_when_check: Just check the size of the expected file when enabled. Default is False.
        :type soft_mode_when_check: bool
        :param tmpdir: Use custom temporary Directory.
        :type tmpdir: Optional[str]
        :param show_all: Show all files, including hidden files.
        :type show_all: bool

        :raises NoRemotePathAssignedWithDownload: If no remote path in repository is assigned.
        """
        configure_http_backend(get_requests_session)

        if tmpdir:
            os.environ['TMPDIR'] = tmpdir

        if not file_in_repo and not archive_in_repo and not dir_in_repo:
            raise NoRemotePathAssignedWithDownload('No remote path in repository assigned.\n'
                                                   'One of the -f, -a, or -d option is required.')

        if file_in_repo:
            if archive_in_repo:
                warnings.warn('File in repository assigned, value of -a option will be ignored.')
            if dir_in_repo:
                warnings.warn('File in repository assigned, value of -d option will be ignored.')
            download_file_to_file(
                local_file=output_path,
                repo_id=repo_id,
                file_in_repo=file_in_repo,
                repo_type=repo_type,
                revision=revision,
            )

        elif archive_in_repo:
            if dir_in_repo:
                warnings.warn('Archive in repository assigned, value of -d option will be ignored.')
            download_archive_as_directory(
                local_directory=output_path,
                repo_id=repo_id,
                file_in_repo=archive_in_repo,
                repo_type=repo_type,
                revision=revision,
                password=password,
            )

        elif dir_in_repo:
            download_directory_as_directory(
                local_directory=output_path,
                repo_id=repo_id,
                dir_in_repo=dir_in_repo,
                pattern=wildcard or '**/*',
                repo_type=repo_type,
                revision=revision,
                silent=False,
                max_workers=max_workers,
                soft_mode_when_check=soft_mode_when_check,
                ignore_patterns=_IGNORE_PATTERN_UNSET if not show_all else [],
            )

        else:
            assert False, 'Should not reach this line, it must be a bug!'  # pragma: no cover

    return cli

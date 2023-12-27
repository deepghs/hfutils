import warnings
from typing import Optional

import click

from .base import CONTEXT_SETTINGS, command_wrap, ClickErrorException
from ..operate import download_file_to_file, download_archive_as_directory, download_directory_as_directory
from ..operate.base import REPO_TYPES, RepoTypeTyping


class NoRemotePathAssignedWithDownload(ClickErrorException):
    """
    Custom exception class for indicating that no remote path in the repository is assigned.
    """
    exit_code = 0x11


def _add_download_subcommand(cli: click.Group) -> click.Group:
    """
    Add the 'download' subcommand to the CLI.

    :param cli: The Click CLI application.
    :type cli: click.Group
    :return: The modified Click CLI application.
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
    @command_wrap()
    def download(repo_id: str, repo_type: RepoTypeTyping,
                 file_in_repo: Optional[str], archive_in_repo: Optional[str], dir_in_repo: Optional[str],
                 output_path: str, revision: str, max_workers: int):
        """
        Download data from HuggingFace repositories.

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
        """
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
            )

        elif dir_in_repo:
            download_directory_as_directory(
                local_directory=output_path,
                repo_id=repo_id,
                dir_in_repo=dir_in_repo,
                repo_type=repo_type,
                revision=revision,
                silent=False,
                max_workers=max_workers,
            )

        else:
            assert False, 'Should not reach this line, it must be a bug!'  # pragma: no cover

    return cli

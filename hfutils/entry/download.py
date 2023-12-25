import warnings
from typing import Optional

import click

from .base import CONTEXT_SETTINGS, command_wrap, ClickErrorException
from ..operate import download_file_to_file, download_archive_as_directory, download_directory_as_directory
from ..operate.base import REPO_TYPES, RepoTypeTyping


class NoRemotePathAssigned(ClickErrorException):
    exit_code = 0x11


def _add_download_subcommand(cli: click.Group) -> click.Group:
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
    @command_wrap()
    def download(repo_id: str, repo_type: RepoTypeTyping,
                 file_in_repo: Optional[str], archive_in_repo: Optional[str], dir_in_repo: Optional[str],
                 output_path: str, revision: str):
        if not file_in_repo and not archive_in_repo and not dir_in_repo:
            raise NoRemotePathAssigned('No remote path in repository assigned.\n'
                                       'One of the -f, -a or -d option is required.')

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
                silent=False,
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
                silent=False,
            )

        elif dir_in_repo:
            download_directory_as_directory(
                local_directory=output_path,
                repo_id=repo_id,
                dir_in_repo=dir_in_repo,
                repo_type=repo_type,
                revision=revision,
                silent=False,
            )

        else:
            assert False, 'Should not reach this line, it must be a bug!'  # pragma: no cover

    return cli

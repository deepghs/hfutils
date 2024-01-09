import warnings
from typing import Optional

import click

from .base import CONTEXT_SETTINGS, command_wrap, ClickErrorException
from ..operate import upload_file_to_file, upload_directory_as_archive, upload_directory_as_directory
from ..operate.base import REPO_TYPES, RepoTypeTyping, get_hf_client


class NoRemotePathAssignedWithUpload(ClickErrorException):
    """
    Custom exception class for indicating that no remote path in the repository is assigned.
    """
    exit_code = 0x21


def _add_upload_subcommand(cli: click.Group) -> click.Group:
    """
    Add the 'upload' subcommand to the CLI.

    :param cli: The Click CLI application.
    :type cli: click.Group
    :return: The modified Click CLI application.
    :rtype: click.Group
    """

    @cli.command('upload', help='Upload data from HuggingFace.\n\n'
                                'Set environment $HF_TOKEN to use your own access token.',
                 context_settings=CONTEXT_SETTINGS)
    @click.option('-r', '--repository', 'repo_id', type=str, required=True,
                  help='Repository to upload to.')
    @click.option('-t', '--type', 'repo_type', type=click.Choice(REPO_TYPES), default='dataset',
                  help='Type of the HuggingFace repository.', show_default=True)
    @click.option('-f', '--filename', 'file_in_repo', type=str, default=None,
                  help='File in repository to upload.')
    @click.option('-a', '--archive', 'archive_in_repo', type=str, default=None,
                  help='Archive file in repository to upload and extract from')
    @click.option('-d', '--directory', 'dir_in_repo', type=str, default=None,
                  help='Directory in repository to upload the full directory tree.')
    @click.option('-i', '--input', 'input_path', type=str, required=True,
                  help='Input path for upload.')
    @click.option('-R', '--revision', 'revision', type=str, default='main',
                  help='Revision of repository.', show_default=True)
    @click.option('-c', '--clear', 'clear', is_flag=True, type=bool, default=False,
                  help='Clear the remote directory before uploading.\n'
                       'Only applied when -d is used.', show_default=True)
    @click.option('-p', '--private', 'private', is_flag=True, type=bool, default=None,
                  help='Set private repository when created.', show_default=True)
    @click.option('-P', '--public', 'public', is_flag=True, type=bool, default=None,
                  help='Set public repository when created.', show_default=True)
    @command_wrap()
    def upload(repo_id: str, repo_type: RepoTypeTyping,
               file_in_repo: Optional[str], archive_in_repo: Optional[str], dir_in_repo: Optional[str],
               input_path: str, revision: str, clear: bool, private: bool, public: bool):
        """
        Upload data to HuggingFace repositories.

        :param repo_id: Repository to upload to.
        :type repo_id: str
        :param repo_type: Type of the HuggingFace repository.
        :type repo_type: RepoTypeTyping
        :param file_in_repo: File in repository to upload.
        :type file_in_repo: Optional[str]
        :param archive_in_repo: Archive file in repository to upload and extract from.
        :type archive_in_repo: Optional[str]
        :param dir_in_repo: Directory in repository to upload the full directory tree.
        :type dir_in_repo: Optional[str]
        :param input_path: Input path for upload.
        :type input_path: str
        :param revision: Revision of repository.
        :type revision: str
        :param clear: Clear the remote directory before uploading.
                      Only applied when -d is used.
        :type clear: bool
        :param private: Set private repository when created.
        :type private: bool
        :param public: Set public repository when created.
        :type public: bool
        """
        if not file_in_repo and not archive_in_repo and not dir_in_repo:
            raise NoRemotePathAssignedWithUpload('No remote path in repository assigned.\n'
                                                 'One of the -f, -a, or -d option is required.')

        hf_client = get_hf_client()
        if private or public:
            set_visibility = True
            if private and public:
                raise ValueError('Repository should have only one accessibility, '
                                 '-p (--private) and -P (--public) should not be used together.')

            is_private = False
            if public:
                is_private = False
            if private:
                is_private = True
        else:
            set_visibility = False
            is_private = False

        if not hf_client.repo_exists(repo_id, repo_type=repo_type):
            hf_client.create_repo(repo_id, repo_type=repo_type, exist_ok=True, private=is_private)
        if set_visibility:
            hf_client.update_repo_visibility(repo_id, repo_type=repo_type, private=is_private)

        if file_in_repo:
            if archive_in_repo:
                warnings.warn('File in repository assigned, value of -a option will be ignored.')
            if dir_in_repo:
                warnings.warn('File in repository assigned, value of -d option will be ignored.')
            upload_file_to_file(
                local_file=input_path,
                repo_id=repo_id,
                file_in_repo=file_in_repo,
                repo_type=repo_type,
                revision=revision,
            )

        elif archive_in_repo:
            if dir_in_repo:
                warnings.warn('Archive in repository assigned, value of -d option will be ignored.')
            upload_directory_as_archive(
                local_directory=input_path,
                repo_id=repo_id,
                archive_in_repo=archive_in_repo,
                repo_type=repo_type,
                revision=revision,
                silent=False,
            )

        elif dir_in_repo:
            upload_directory_as_directory(
                local_directory=input_path,
                repo_id=repo_id,
                path_in_repo=dir_in_repo,
                repo_type=repo_type,
                revision=revision,
                clear=clear,
            )

        else:
            assert False, 'Should not reach this line, it must be a bug!'  # pragma: no cover

    return cli

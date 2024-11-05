"""
This module provides functionality for uploading data to HuggingFace repositories.

It includes a CLI command for uploading files, archives, or directories to HuggingFace
repositories. The module handles different upload scenarios, including creating new
repositories, setting visibility, and handling various input types.

Usage:
    This module is typically used as part of a larger CLI application for interacting
    with HuggingFace repositories.
"""

import warnings
from typing import Optional

import click
from huggingface_hub import configure_http_backend

from .base import CONTEXT_SETTINGS, command_wrap, ClickErrorException
from ..operate import upload_file_to_file, upload_directory_as_archive, upload_directory_as_directory
from ..operate.base import REPO_TYPES, RepoTypeTyping, get_hf_client
from ..utils import get_requests_session


class NoRemotePathAssignedWithUpload(ClickErrorException):
    """
    Custom exception class for indicating that no remote path in the repository is assigned.

    This exception is raised when attempting to upload without specifying a remote path
    (file, archive, or directory) in the repository.

    :attribute exit_code: The exit code to be used when this exception is raised.
    :type exit_code: int
    """
    exit_code = 0x21


def _add_upload_subcommand(cli: click.Group) -> click.Group:
    """
    Add the 'upload' subcommand to the CLI.

    This function defines and adds the 'upload' command to the provided CLI group.
    It sets up all the necessary options and implements the upload functionality.

    :param cli: The Click CLI application to which the upload command will be added.
    :type cli: click.Group
    :return: The modified Click CLI application with the upload command added.
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
    @click.option('-w', '--wildcard', 'wildcard', type=str, default=None,
                  help='Wildcard for files to download. Only applied when -d is used.', show_default=True)
    @click.option('-m', '--message', 'message', type=str, default=None,
                  help='Commit message for this operation.', show_default=True)
    @command_wrap()
    def upload(repo_id: str, repo_type: RepoTypeTyping,
               file_in_repo: Optional[str], archive_in_repo: Optional[str], dir_in_repo: Optional[str],
               input_path: str, revision: str, clear: bool, private: bool, public: bool, wildcard: Optional[str],
               message: Optional[str]):
        """
        Upload data to HuggingFace repositories.

        This function handles the upload process to HuggingFace repositories. It supports
        uploading individual files, archives, or entire directories. The function also
        manages repository creation and visibility settings.

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
        :param wildcard: Wildcard pattern for selecting files to upload.
        :type wildcard: Optional[str]
        :param message: Commit message for this operation.
        :type message: Optional[str]

        :raises NoRemotePathAssignedWithUpload: If no remote path in repository is assigned.
        :raises ValueError: If both private and public flags are set.
        """
        configure_http_backend(get_requests_session)

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
                message=message,
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
                pattern=wildcard,
                silent=False,
                message=message,
            )

        elif dir_in_repo:
            upload_directory_as_directory(
                local_directory=input_path,
                repo_id=repo_id,
                path_in_repo=dir_in_repo,
                repo_type=repo_type,
                revision=revision,
                clear=clear,
                pattern=wildcard,
                message=message,
            )

        else:
            assert False, 'Should not reach this line, it must be a bug!'  # pragma: no cover

    return cli

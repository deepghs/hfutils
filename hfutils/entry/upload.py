"""
This module provides functionality for uploading data to HuggingFace repositories.

It includes a CLI command for uploading files, archives, or directories to HuggingFace
repositories. The module handles different upload scenarios, including creating new
repositories, setting visibility, and handling various input types.

Usage:
    This module is typically used as part of a larger CLI application for interacting
    with HuggingFace repositories. It requires appropriate authentication through
    HuggingFace tokens (set via environment variable HF_TOKEN).
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
    (file, archive, or directory) in the repository. At least one of these options must
    be provided for successful upload operation.

    :attribute exit_code: The exit code to be used when this exception is raised.
    :type exit_code: int
    """
    exit_code = 0x21


def _add_upload_subcommand(cli: click.Group) -> click.Group:
    """
    Add the 'upload' subcommand to the CLI application.

    This function enhances the provided CLI group by adding a comprehensive upload command
    that supports various upload scenarios to HuggingFace repositories. It configures
    multiple options for fine-grained control over the upload process.

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
    @click.option('-s', '--max_size_per_pack', 'max_size_per_pack', type=str, default=None,
                  help='Max size per archive packages, only applied when -a is assigned.', show_default=True)
    @command_wrap()
    def upload(repo_id: str, repo_type: RepoTypeTyping,
               file_in_repo: Optional[str], archive_in_repo: Optional[str], dir_in_repo: Optional[str],
               input_path: str, revision: str, clear: bool, private: bool, public: bool, wildcard: Optional[str],
               message: Optional[str], max_size_per_pack: Optional[str]):
        """
        Upload data to HuggingFace repositories with various options and modes.

        This function implements the core upload functionality, supporting multiple upload modes
        and repository management features. It handles repository creation, visibility settings,
        and different types of uploads (file, archive, directory).

        :param repo_id: Repository identifier to upload to.
        :type repo_id: str
        :param repo_type: Type of the HuggingFace repository (e.g., dataset, model).
        :type repo_type: RepoTypeTyping
        :param file_in_repo: Target path for single file upload in the repository.
        :type file_in_repo: Optional[str]
        :param archive_in_repo: Target path for archive upload in the repository.
        :type archive_in_repo: Optional[str]
        :param dir_in_repo: Target directory path in the repository for directory upload.
        :type dir_in_repo: Optional[str]
        :param input_path: Local path of the file or directory to upload.
        :type input_path: str
        :param revision: Repository revision/branch to upload to.
        :type revision: str
        :param clear: Whether to clear existing content before directory upload.
        :type clear: bool
        :param private: Flag to set repository as private when created.
        :type private: bool
        :param public: Flag to set repository as public when created.
        :type public: bool
        :param wildcard: Pattern for filtering files during upload.
        :type wildcard: Optional[str]
        :param message: Commit message for the upload operation.
        :type message: Optional[str]
        :param max_size_per_pack: Maximum size limit for archive packages.
        :type max_size_per_pack: Optional[str]

        :raises NoRemotePathAssignedWithUpload: If no upload mode is specified.
        :raises ValueError: If conflicting visibility settings are provided.
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
                max_size_per_pack=max_size_per_pack,
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

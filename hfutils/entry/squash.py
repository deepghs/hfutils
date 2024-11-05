"""
This module provides a command-line interface (CLI) for managing Hugging Face repositories.
It includes functionality to squash the history of a specified repository on Hugging Face.
Users can specify the repository ID, type, revision, and commit message when executing the squash command.
The module utilizes the Click library for creating the CLI and integrates with the Hugging Face Hub API.
"""

from typing import Optional

import click
from huggingface_hub import configure_http_backend

from .base import CONTEXT_SETTINGS, command_wrap
from ..operate.base import REPO_TYPES, RepoTypeTyping, get_hf_client
from ..utils import get_requests_session, hf_fs_path


def _add_squash_subcommand(cli: click.Group) -> click.Group:
    """
    Add a 'squash' subcommand to the provided CLI group.

    This subcommand allows users to squash the commit history of a specified Hugging Face repository.
    Users must provide the repository ID and can optionally specify the repository type, revision, and commit message.
    The command configures the HTTP backend and uses the Hugging Face client to perform the squash operation.

    :param cli: The click.Group instance to which the subcommand will be added.
    :type cli: click.Group

    :return: The updated click.Group instance with the 'squash' subcommand added.
    :rtype: click.Group
    """

    @cli.command('squash', help='Squash Repository from HuggingFace.\n\n'
                                'Set environment $HF_TOKEN to use your own access token.',
                 context_settings=CONTEXT_SETTINGS)
    @click.option('-r', '--repository', 'repo_id', type=str, required=True,
                  help='Repository to upload to.')
    @click.option('-t', '--type', 'repo_type', type=click.Choice(REPO_TYPES), default='dataset',
                  help='Type of the HuggingFace repository.', show_default=True)
    @click.option('-R', '--revision', 'revision', type=str, default='main',
                  help='Revision of repository.', show_default=True)
    @click.option('-m', '--message', 'message', type=str, default=None,
                  help='Commit message for this operation.', show_default=True)
    @command_wrap()
    def squash(repo_id: str, repo_type: RepoTypeTyping, revision: str, message: Optional[str]):
        """
        Squash the commit history of the specified Hugging Face repository.

        This function configures the HTTP backend, initializes the Hugging Face client,
        and performs the squash operation on the repository. If no commit message is provided,
        a default message is generated using the repository ID and type.

        :param repo_id: The ID of the repository to squash.
        :type repo_id: str
        :param repo_type: The type of the Hugging Face repository (e.g., 'dataset', 'model').
        :type repo_type: RepoTypeTyping
        :param revision: The branch or revision of the repository to squash.
        :type revision: str
        :param message: Optional commit message for the squash operation.
        :type message: Optional[str]
        """
        configure_http_backend(get_requests_session)
        hf_client = get_hf_client()
        hf_client.super_squash_history(
            repo_id=repo_id,
            repo_type=repo_type,
            branch=revision,
            commit_message=message or f'Squash {hf_fs_path(repo_id=repo_id, repo_type=repo_type, filename="")!r}',
        )

    return cli

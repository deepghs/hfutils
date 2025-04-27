"""
HuggingFace Repository Duplication Module

This module provides functionality for duplicating repositories on HuggingFace Hub via command line interface.
It includes commands and utilities to copy repositories while preserving their content and structure.
"""

import click
from huggingface_hub import configure_http_backend

from .base import CONTEXT_SETTINGS, command_wrap
from ..operate import hf_repo_duplicate
from ..operate.base import REPO_TYPES, RepoTypeTyping
from ..utils import get_requests_session


def _add_duplicate_subcommand(cli: click.Group) -> click.Group:
    """
    Add the duplicate subcommand to the CLI group.

    This function adds a 'duplicate' command to the provided Click CLI group that enables
    repository duplication on HuggingFace Hub. It configures all necessary options and
    handles the execution flow.

    :param cli: The Click command group to add the duplicate command to
    :type cli: click.Group

    :return: The modified CLI group with the duplicate command added
    :rtype: click.Group
    """

    @cli.command('duplicate', help='Duplicate Repository on HuggingFace.\n\n'
                                   'Set environment $HF_TOKEN to use your own access token.',
                 context_settings=CONTEXT_SETTINGS)
    @click.option('-r', '--src_repo', 'src_repo_id', type=str, required=True,
                  help='Repository to be duplicated.')
    @click.option('-R', '--dst_repo', 'dst_repo_id', type=str, required=True,
                  help='Repository to duplicate to.')
    @click.option('-t', '--type', 'repo_type', type=click.Choice(REPO_TYPES), default='dataset',
                  help='Type of the HuggingFace repository.', show_default=True)
    @click.option('--private', 'private', type=bool, is_flag=True, default=False,
                  help='Duplicate as a private repository.')
    @command_wrap()
    def duplicate(src_repo_id: str, dst_repo_id: str, repo_type: RepoTypeTyping, private: bool):
        """
        Duplicate a HuggingFace repository to a new location.

        This command duplicates an existing HuggingFace repository to a new destination,
        with options to specify the repository type and visibility settings.

        :param src_repo_id: The source repository ID to duplicate from
        :type src_repo_id: str
        :param dst_repo_id: The destination repository ID to duplicate to
        :type dst_repo_id: str
        :param repo_type: The type of repository (dataset, model, etc.)
        :type repo_type: RepoTypeTyping
        :param private: Whether the duplicated repository should be private
        :type private: bool

        :raises: Various exceptions from huggingface_hub based on operation status
        """
        configure_http_backend(get_requests_session)
        hf_repo_duplicate(
            src_repo_id=src_repo_id,
            dst_repo_id=dst_repo_id,
            repo_type=repo_type,
            private=private,
        )

    return cli

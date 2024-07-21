import logging

import click

from .base import CONTEXT_SETTINGS
from ..operate.base import REPO_TYPES, RepoTypeTyping
from ..repository import hf_hub_rollback
from ..utils import ColoredFormatter


def _add_rollback_subcommand(cli: click.Group) -> click.Group:
    """
    Add a 'rollback' subcommand to the given CLI group.

    This function defines a 'rollback' command that allows users to rollback
    repositories on the Hugging Face Hub to a specific commit.

    :param cli: The Click group to which the 'rollback' command will be added.
    :type cli: click.Group
    :return: The modified Click group with the 'rollback' command added.
    :rtype: click.Group
    """

    @cli.command('rollback', help='Rollback remote repository to a specific commit.\n\n'
                                  'Set environment $HF_TOKEN to use your own access token.',
                 context_settings=CONTEXT_SETTINGS)
    @click.option('-r', '--repository', 'repo_id', type=str, required=True,
                  help='Repository to rollback.')
    @click.option('-t', '--type', 'repo_type', type=click.Choice(REPO_TYPES), default='dataset',
                  help='Type of the HuggingFace repository.', show_default=True)
    @click.option('-R', '--revision', 'revision', type=str, default='main',
                  help='Revision of repository.', show_default=True)
    @click.option('-c', '--commit_id', 'rollback_to_commit_id', type=str, required=True,
                  help='Rollback back to this commit id.')
    def rollback(repo_id: str, repo_type: RepoTypeTyping, revision: str, rollback_to_commit_id: str):
        """
        Rollback a repository on the Hugging Face Hub to a specific commit.

        This function sets up logging and then calls hf_hub_rollback to perform the actual rollback.

        :param repo_id: The ID of the repository to rollback.
        :param repo_type: The type of the repository (e.g., 'dataset', 'model').
        :param revision: The revision of the repository to rollback.
        :param rollback_to_commit_id: The commit ID to rollback to.
        """
        # Set up logging
        logger = logging.getLogger()
        logger.setLevel(logging.INFO)
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(ColoredFormatter())
        logger.addHandler(console_handler)

        # Perform the rollback operation
        hf_hub_rollback(
            repo_id=repo_id,
            repo_type=repo_type,
            revision=revision,
            rollback_to=rollback_to_commit_id,
        )

    return cli

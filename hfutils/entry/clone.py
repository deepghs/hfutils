import logging
import os.path
import re
from typing import Optional

import click

from .base import CONTEXT_SETTINGS
from ..operate.base import REPO_TYPES, RepoTypeTyping
from ..repository import hf_hub_clone
from ..utils import ColoredFormatter


def _add_clone_subcommand(cli: click.Group) -> click.Group:
    """
    Add a 'clone' subcommand to the given CLI group.

    This function defines a 'clone' command that allows users to clone repositories
    from the Hugging Face Hub.

    :param cli: The Click group to which the 'clone' command will be added.
    :type cli: click.Group
    :return: The modified Click group with the 'clone' command added.
    :rtype: click.Group
    """

    @cli.command('clone', help='Clone remote repository with permission (if possible).\n\n'
                               'Set environment $HF_TOKEN to use your own access token.',
                 context_settings=CONTEXT_SETTINGS)
    @click.option('-r', '--repository', 'repo_id', type=str, required=True,
                  help='Repository to clone.')
    @click.option('-t', '--type', 'repo_type', type=click.Choice(REPO_TYPES), default='dataset',
                  help='Type of the HuggingFace repository.', show_default=True)
    @click.option('-R', '--revision', 'revision', type=str, default='main',
                  help='Revision of repository.', show_default=True)
    @click.option('-o', '--output_dir', 'output_dir', type=str, default=None,
                  help='Output directory to clone the repository')
    @click.option('--no_lfs', 'no_lfs', type=bool, is_flag=True, default=False,
                  help='Do not download LFS files, just download their pointers.')
    @click.option('-d', '--max_depth', 'max_depth', type=int, default=None,
                  help='Max commit depth to clone. Useful when this repository has large numbers of commits.')
    def clone(repo_id: str, repo_type: RepoTypeTyping, revision: str, output_dir: Optional[str] = None,
              no_lfs: bool = False, max_depth: Optional[int] = None):
        """
        Clone a repository from the Hugging Face Hub.

        This function sets up logging and then calls hf_hub_clone to perform the actual cloning.

        :param repo_id: The ID of the repository to clone.
        :param repo_type: The type of the repository (e.g., 'dataset', 'model').
        :param revision: The revision of the repository to clone.
        :param output_dir: The directory where the repository will be cloned. If None, uses the repo's short name.
        :param no_lfs: If True, don't download LFS files, just their pointers.
        :param max_depth: The maximum depth of commits to clone.
        """
        # Set up logging
        logger = logging.getLogger()
        logger.setLevel(logging.INFO)
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(ColoredFormatter())
        logger.addHandler(console_handler)

        # Determine the output directory
        short_name = list(filter(bool, re.split(r'[/\\]+', repo_id)))[-1]
        output_dir = os.path.abspath(output_dir or short_name)
        if os.path.dirname(output_dir):
            os.makedirs(os.path.dirname(output_dir), exist_ok=True)

        # Perform the clone operation
        hf_hub_clone(
            repo_id=repo_id,
            repo_type=repo_type,
            revision=revision,
            dst_dir=output_dir,
            no_lfs=no_lfs,
            max_depth=max_depth,
        )

    return cli

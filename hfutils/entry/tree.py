import mimetypes

import click
from huggingface_hub import configure_http_backend
from hbutils.string import format_tree
from .base import CONTEXT_SETTINGS
from ..operate.base import REPO_TYPES, get_hf_client, list_files_in_repository, RepoTypeTyping
from ..utils import get_requests_session


def _add_tree_subcommand(cli: click.Group) -> click.Group:
    @cli.command('tree', help='List files from HuggingFace repository.\n\n'
                              'Set environment $HF_TOKEN to use your own access token.',
                 context_settings=CONTEXT_SETTINGS)
    @click.option('-r', '--repository', 'repo_id', type=str, required=True,
                  help='Repository to download from.')
    @click.option('-t', '--type', 'repo_type', type=click.Choice(REPO_TYPES), default='dataset',
                  help='Type of the HuggingFace repository.', show_default=True)
    @click.option('-d', '--directory', 'dir_in_repo', type=str, default=None,
                  help='Directory in repository to download the full directory tree.')
    @click.option('-R', '--revision', 'revision', type=str, default='main',
                  help='Revision of repository.', show_default=True)
    @click.option('-a', '--all', 'show_all', is_flag=True, type=bool, default=False,
                  help='Show all files, including hidden files.', show_default=True)
    def tree(repo_id: str, repo_type: RepoTypeTyping, dir_in_repo, revision: str, show_all: bool):
        configure_http_backend(get_requests_session)

        hf_client = get_hf_client()

        list_files_in_repository(
            repo_id=repo_id,
            repo_type=repo_type,
            subdir='.',
            revision=revision,
            ignore_patterns=[],

        )

    return cli

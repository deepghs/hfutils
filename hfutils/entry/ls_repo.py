import fnmatch
from typing import Optional

import click
from huggingface_hub import configure_http_backend
from huggingface_hub.utils import LocalTokenNotFoundError

from .base import CONTEXT_SETTINGS, ClickErrorException
from ..operate.base import REPO_TYPES, get_hf_client
from ..utils import get_requests_session


class NoLocalAuthentication(ClickErrorException):
    """
    Exception raised when there is no local authentication token.
    """
    exit_code = 0x31


def _add_ls_repo_subcommand(cli: click.Group) -> click.Group:
    """
    Add the ls_repo subcommand to the CLI.

    :param cli: The click Group object.
    :type cli: click.Group

    :return: The updated click Group object.
    :rtype: click.Group
    """

    @cli.command('ls_repo', help='List repositories from HuggingFace.\n\n'
                                 'Set environment $HF_TOKEN to use your own access token.',
                 context_settings=CONTEXT_SETTINGS)
    @click.option('-a', '--author', 'author', type=str, default=None,
                  help='Author of the repositories. Search my repositories when not given.')
    @click.option('-t', '--type', 'repo_type', type=click.Choice(REPO_TYPES), default='dataset',
                  help='Type of the HuggingFace repository.', show_default=True)
    @click.option('-p', '--pattern', 'pattern', type=str, default='*',
                  help='Pattern of the repository names.', show_default=True)
    def ls(author: Optional[str], repo_type: str, pattern: str):
        """
        List repositories from HuggingFace.

        :param author: Author of the repositories.
        :type author: Optional[str]
        :param repo_type: Type of the HuggingFace repository.
        :type repo_type: str
        :param pattern: Pattern of the repository names.
        :type pattern: str
        """
        configure_http_backend(get_requests_session)

        hf_client = get_hf_client()
        if not author:
            try:
                info = hf_client.whoami()
                author = author or info['name']
            except LocalTokenNotFoundError:
                raise NoLocalAuthentication(
                    'Authentication failed.\n'
                    'Make sure you have set the correct Huggingface token.\n'
                    'Or if need to use this with guest mode, please explicitly set the `-a` option.'
                )

        if repo_type == 'model':
            r = hf_client.list_models(author=author)
        elif repo_type == 'dataset':
            r = hf_client.list_datasets(author=author)
        elif repo_type == 'space':
            r = hf_client.list_spaces(author=author)
        else:
            raise ValueError(f'Unknown repository type - {repo_type!r}.')  # pragma: no cover

        for repo_item in r:
            if fnmatch.fnmatch(repo_item.id, pattern):
                print(repo_item.id)

    return cli

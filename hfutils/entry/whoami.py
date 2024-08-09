import click
from hbutils.string import plural_word
from huggingface_hub import configure_http_backend
from huggingface_hub.utils import LocalTokenNotFoundError

from .base import CONTEXT_SETTINGS
from ..operate.base import get_hf_client
from ..utils import get_requests_session


def _add_whoami_subcommand(cli: click.Group) -> click.Group:
    """
    Add the 'whoami' subcommand to the CLI.

    This command displays the current identification.

    :param cli: The Click CLI application.
    :type cli: click.Group
    :return: The modified Click CLI application.
    :rtype: click.Group
    """

    @cli.command('whoami', help='See the current identification.\n\n'
                                'Set environment $HF_TOKEN to use your own access token.',
                 context_settings=CONTEXT_SETTINGS)
    def whoami():
        """
        Display the current identification.

        This function retrieves the current user's identification from the Hugging Face Hub API and displays it.

        """
        configure_http_backend(get_requests_session)

        hf_client = get_hf_client()
        try:
            info = hf_client.whoami()
            username = info['name']
            click.echo(f'Hi, {click.style(f"@{username}", fg="green", bold=True)} '
                       f'(full name: {click.style(info["fullname"], underline=True)}'
                       f'{", PRO" if info["isPro"] else ""}).')
            click.echo(f'You can access all resources with this identification.')
            if info['orgs']:
                click.echo(f'You have entered {plural_word(len(info["orgs"]), "organizations")}:')
                for i, org_item in enumerate(info['orgs'], start=1):
                    click.echo(f'{i}. {click.style("@" + org_item["name"], fg="blue", bold=True)} '
                               f'(full name: {click.style(org_item["fullname"], underline=True)})')
        except LocalTokenNotFoundError:
            click.echo(f'Hi, {click.style("Guest", fg="yellow", bold=True)} (not authenticated).')
            click.echo(click.style(f'No token for huggingface authentication found.', underline=True))
            click.echo(f'If you need to access more, just set `HF_TOKEN` environment variable, '
                       f'or use `huggingface-cli login`.')

    return cli

import click
from hbutils.string import plural_word
from huggingface_hub.utils import LocalTokenNotFoundError

from .base import CONTEXT_SETTINGS
from ..meta import hf_site_info
from ..operate.base import get_hf_client
from ..utils import get_requests_session, HF_IS_VERSION_0_X_X

if HF_IS_VERSION_0_X_X:
    from huggingface_hub import configure_http_backend
else:
    configure_http_backend = None


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
        if HF_IS_VERSION_0_X_X:
            configure_http_backend(get_requests_session)

        hf_client = get_hf_client()
        try:
            if not hf_client.token:
                raise LocalTokenNotFoundError

            info = hf_client.whoami()
            username = info['name']
            click.echo(f'Hi, {click.style(f"@{username}", fg="green", bold=True)} '
                       f'(full name: {click.style(info["fullname"], underline=True)}'
                       f'{", PRO" if info["isPro"] else ""}).')

            site_info = hf_site_info()
            if site_info.api == 'huggingface' and site_info.version == 'official':
                click.echo(f'Connected to {click.style(site_info.name, fg="yellow", bold=True)}.')
            elif site_info.api == 'huggingface':
                click.echo(f'Connected to {click.style(site_info.name, fg="bright_yellow", bold=True)} '
                           f'({click.style(site_info.endpoint, fg="bright_blue", underline=True)}).')
            else:
                click.echo(f'Connected to {click.style(site_info.name, fg="magenta", bold=True)} '
                           f'(backend: {click.style(f"{site_info.api} v{site_info.version}", fg="cyan")} '
                           f'at {click.style(site_info.endpoint, fg="bright_blue", underline=True)}).')

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

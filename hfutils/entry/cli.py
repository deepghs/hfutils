from .dispatch import hfutilcli
from .download import _add_download_subcommand

_DECORATORS = [
    _add_download_subcommand
]

cli = hfutilcli
for deco in _DECORATORS:
    cli = deco(cli)

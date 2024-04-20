from .dispatch import hfutilcli
from .download import _add_download_subcommand
from .upload import _add_upload_subcommand

_DECORATORS = [
    _add_download_subcommand,
    _add_upload_subcommand,
]

cli = hfutilcli
for deco in _DECORATORS:
    cli = deco(cli)

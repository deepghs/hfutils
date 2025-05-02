from .clone import _add_clone_subcommand
from .dispatch import hfutilcli
from .download import _add_download_subcommand
from .duplicate import _add_duplicate_subcommand
from .ils import _add_ils_subcommand
from .index import _add_index_subcommand
from .ls import _add_ls_subcommand
from .ls_repo import _add_ls_repo_subcommand
from .rollback import _add_rollback_subcommand
from .squash import _add_squash_subcommand
from .tree import _add_tree_subcommand
from .upload import _add_upload_subcommand
from .warmup import _add_warmup_subcommand
from .whoami import _add_whoami_subcommand

_DECORATORS = [
    _add_download_subcommand,
    _add_upload_subcommand,
    _add_ls_subcommand,
    _add_whoami_subcommand,
    _add_ls_repo_subcommand,
    _add_index_subcommand,
    _add_rollback_subcommand,
    _add_clone_subcommand,
    _add_tree_subcommand,
    _add_ils_subcommand,
    _add_squash_subcommand,
    _add_duplicate_subcommand,
    _add_warmup_subcommand,
]

cli = hfutilcli
for deco in _DECORATORS:
    cli = deco(cli)

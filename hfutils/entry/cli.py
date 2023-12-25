from .dispatch import hfutilcli

_DECORATORS = [

]

cli = hfutilcli
for deco in _DECORATORS:
    cli = deco(cli)

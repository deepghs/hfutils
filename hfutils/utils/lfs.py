"""
Overview:
    Access to the LFS information of a file listed by ``huggingface_hub``.
"""
from typing import Any, Optional


def lfs_attr(lfs: Any, name: str) -> Optional[Any]:
    """
    Read one field (``size``, ``sha256`` or ``pointer_size``) of the LFS information of a repository file.

    ``huggingface_hub`` 0.20 returns that information as a plain ``dict``, newer versions as an object with attributes.

    :param lfs: The ``lfs`` field of :class:`huggingface_hub.hf_api.RepoFile`, a ``dict``, an object or ``None``.
    :param name: Name of the field.
    :return: The value, or ``None`` when there is no LFS information.

    Example::

        >>> lfs_attr({'size': 12, 'sha256': 'abc'}, 'size')
        12
        >>> lfs_attr(None, 'size') is None
        True
    """
    if not lfs:
        return None
    if isinstance(lfs, dict):
        return lfs.get(name)
    return getattr(lfs, name)

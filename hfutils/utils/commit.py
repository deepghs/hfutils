"""
Overview:
    Access to the last commit information of a file listed by ``huggingface_hub``.
"""
from datetime import datetime
from typing import Any


def last_commit_attr(commit: Any, name: str) -> Any:
    """
    Read one field (``oid``, ``title`` or ``date``) of the last commit of a repository file or folder.

    ``huggingface_hub`` 0.20 returns it as a plain ``dict`` whose ``date`` is an ISO string, newer versions as an
    object whose ``date`` is a :class:`datetime.datetime`. ``date`` is always returned as a ``datetime``.

    :param commit: The ``last_commit`` field of :class:`huggingface_hub.hf_api.RepoFile`, a ``dict`` or an object.
    :param name: Name of the field.
    :return: The value.

    Example::

        >>> last_commit_attr({'oid': 'abcdef', 'title': 'hi', 'date': '2024-01-02T03:04:05.000Z'}, 'title')
        'hi'
        >>> last_commit_attr({'oid': 'abcdef', 'title': 'hi', 'date': '2024-01-02T03:04:05.000Z'}, 'date').year
        2024
    """
    value = commit[name] if isinstance(commit, dict) else getattr(commit, name)
    if name == 'date' and isinstance(value, str):
        value = datetime.fromisoformat(value.replace('Z', '+00:00'))
    return value

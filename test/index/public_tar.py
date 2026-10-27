"""
A public indexed tar archive for the tests of the remote functions: ``nyanko7/danbooru2023`` (``original/data-0001.tar``, 8.5 GB,
6775 files) and its index in ``deepghs/danbooru2023_index``.

Nothing about it is hard coded. The expected values come from the index itself (offset, size and sha256 of every member, written
by the tool that built the archive), which these tests download like any other file, and from what is computed with ``hashlib``
on the bytes that a function returned.
"""
import json
import os

import pytest
from huggingface_hub import hf_hub_download

REPO = 'nyanko7/danbooru2023'
ARCHIVE = 'original/data-0001.tar'
IDX_REPO = 'deepghs/danbooru2023_index'
IDX_FILE = 'original/data-0001.json'
OTHER_IDX_FILE = 'original/data-0002.json'  # the index of another archive of the same dataset
EMPTY_MEMBER = '2946001.'  # a member of size 0


def kwargs(**extra):
    """The arguments that every function of ``hfutils.index`` takes to find the archive and its index."""
    return dict(repo_id=REPO, archive_in_repo=ARCHIVE, idx_repo_id=IDX_REPO, **extra)


def load_index(idx_file: str = IDX_FILE) -> dict:
    path = hf_hub_download(IDX_REPO, idx_file, repo_type='dataset')
    with open(path, 'r') as f:
        return json.load(f)


@pytest.fixture()
def index():
    """The index as the tool that built the archive wrote it: ``{'filesize', 'hash', 'hash_lfs', 'files': {name: {...}}}``."""
    return load_index()


@pytest.fixture()
def members(index):
    """Three members to read: the smallest non empty one, a medium one and the empty one."""
    files = {name[2:] if name.startswith('./') else name: info for name, info in index['files'].items()}
    smallest = min((n for n, i in files.items() if i['size'] > 0), key=lambda n: (files[n]['size'], n))
    assert files[EMPTY_MEMBER]['size'] == 0
    return {'small': smallest, 'medium': '1.jpg', 'empty': EMPTY_MEMBER, 'info': files}

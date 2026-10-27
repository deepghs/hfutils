import io
import os
import tarfile

import pytest
from hbutils.system import TemporaryDirectory

from hfutils.index import tar_create_index
from test.testings import get_testfile


def _add(tf: tarfile.TarFile, name: str, data: bytes):
    info = tarfile.TarInfo(name)
    info.size = len(data)
    tf.addfile(info, io.BytesIO(data))


def _build(directory: str, name: str, members):
    """A tar archive with an index next to it (``<name>.tar`` and ``<name>.json``), like the ones of an indexed dataset."""
    tar_file = os.path.join(directory, f'{name}.tar')
    with tarfile.open(tar_file, 'w') as tf:
        for member, source in members:
            with open(source, 'rb') as f:
                _add(tf, member, f.read())
    tar_create_index(tar_file, os.path.join(directory, f'{name}.json'), silent=True)


@pytest.fixture(scope='module')
def local_narugo_test_cos5t_tars():
    """
    The archives that the local fetch tests read: ``mashu_skins.tar`` (the files of ``test/testfile/skin_mashu``, ``.meta.json``
    included), ``ex3.tar`` (one file in a sub directory) and ``empty_file.tar`` (an empty member), each with its index.

    The tests used to download them from a private dataset, but what they test are functions that read a *local* archive, and what
    they compare the results with is already in the repository, so the archives are built here (no network, no private data;
    the name of the fixture stays so that the tests read as they did).
    """
    skin_mashu = get_testfile('skin_mashu')
    with TemporaryDirectory() as td:
        _build(td, 'mashu_skins', [(name, os.path.join(skin_mashu, name)) for name in sorted(os.listdir(skin_mashu))])
        _build(td, 'ex3', [('artoria_caster_third_ascension_fate/sankaku_21305298.jpg', get_testfile('sankaku_21305298.jpg'))])
        empty = os.path.join(td, 'empty.bin')
        open(empty, 'wb').close()
        _build(td, 'empty_file', [('empty_file', empty)])
        os.remove(empty)
        yield td

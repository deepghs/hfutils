"""
pytest plugin of the cassette framework (loaded from ``test/conftest.py``).

* ``--hf-record {none,new,rewrite,live}`` (or ``HFUTILS_VCR_MODE``), see :mod:`.session`.
* every test runs inside its ``main`` segment, in every mode but ``live``.
* the real network is blocked for the whole session in ``none`` mode.
* ``huggingface_hub`` runs in a hermetic configuration, see :mod:`.env`.
"""
import logging
import os
import sys

from .env import REPLAY_TOKEN  # noqa: E402  (also prepares the hermetic environment, see its docstring)

_MODE_ENV = 'HFUTILS_VCR_MODE'

import pytest  # noqa: E402

# VCR.py logs every recorded request at INFO, which tends to write into capture streams that are already closed
logging.getLogger('vcr').setLevel(logging.WARNING)

from .session import HfVcr, HfVcrTest, MODES, safe_name  # noqa: E402


def pytest_addoption(parser):
    group = parser.getgroup('hfvcr', 'Hugging Face cassettes')
    group.addoption('--hf-record', dest='hf_record', choices=MODES, default=os.environ.get(_MODE_ENV, 'none'),
                    help='none: replay only, network blocked (default). new: record missing cassettes. '
                         'rewrite: record again. live: real network, no cassettes.')
    group.addoption('--hf-variant', dest='hf_variant', default=None,
                    help='record into <cassette>@<variant>.json (for a client generation whose requests differ, e.g. '
                         'hub0 for huggingface_hub < 1.0). Replay picks a variant by itself.')


def pytest_configure(config):
    # the environment of env.py is only worth something if huggingface_hub read it
    if 'huggingface_hub' in sys.modules:
        from huggingface_hub import constants
        if not getattr(constants, 'HF_HUB_DISABLE_XET', True):  # versions without Xet need no switch
            raise pytest.UsageError(
                'huggingface_hub was imported before test/testings/hfvcr/env.py ran, so HF_HUB_DISABLE_XET did not '
                'take effect and uploads/downloads would bypass the cassettes. Import test.testings.hfvcr.env '
                'first in every conftest.py that imports huggingface_hub (or hfutils).')
    config.addinivalue_line('markers', 'hf_live: needs the real Hugging Face and is skipped unless --hf-record=live')
    if config.getoption('hf_record') == 'none':
        # a token from the developer's shell must not change what a replay does
        os.environ['HF_TOKEN'] = REPLAY_TOKEN


def client_variant():
    """
    Name of the client generation whose cassettes are preferred, ``None`` for the current one.

    ``hub0`` is ``huggingface_hub`` < 1.0 (``requests``): a few of its operations (the checks before an upload, for one) use
    other endpoints than 1.x and 2.x, so those tests keep a ``@hub0`` cassette next to the default one.
    """
    from importlib.metadata import version
    try:
        major = int(version('huggingface_hub').split('.')[0])
    except Exception:  # noqa
        return None
    return 'hub0' if major < 1 else None


def _read_pending(config):
    path = os.path.join(str(config.rootpath), 'test', 'cassettes', 'PENDING.txt')
    if not os.path.exists(path):
        return {}
    pending, reason = {}, 'cassette not recorded yet'
    with open(path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line.startswith('# reason:'):
                reason = line[len('# reason:'):].strip()
            elif line and not line.startswith('#'):
                pending[line] = reason
    return pending


def pytest_collection_modifyitems(config, items):
    mode = config.getoption('hf_record')
    if mode != 'live':
        skip = pytest.mark.skip(reason='needs --hf-record=live')
        for item in items:
            if 'hf_live' in item.keywords:
                item.add_marker(skip)
    if mode == 'none':
        # tests whose cassette cannot be recorded yet are skipped *visibly*, with the reason
        # (see test/cassettes/README.md); recording modes still run them
        for nodeid, reason in _read_pending(config).items():
            for item in items:
                if item.nodeid == nodeid:
                    item.add_marker(pytest.mark.skip(reason=f'pending cassette: {reason}'))


@pytest.fixture(scope='session')
def hf_vcr_session(request):
    cassette_dir = os.path.join(str(request.config.rootpath), 'test', 'cassettes')
    session = HfVcr(cassette_dir, mode=request.config.getoption('hf_record'),
                    variant=client_variant(), record_variant=request.config.getoption('hf_variant'))
    with session.guard():
        yield session


def _test_key(request) -> str:
    node = request.node
    module = os.path.splitext(os.path.relpath(str(node.fspath), os.path.join(str(request.config.rootpath), 'test')))[0]
    module = module.replace(os.sep, '/')
    name = node.name
    cls = getattr(node, 'cls', None)
    if cls is not None:
        name = f'{cls.__name__}.{name}'
    return f'{module}/{safe_name(name)}'


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    report = outcome.get_result()
    if report.failed:
        item._hf_vcr_failed = True


@pytest.fixture(autouse=True)
def hf_vcr(request, hf_vcr_session):
    """
    Handle of the cassette session of this test; its ``main`` segment wraps the whole test.

    pytest never throws a test's exception into a fixture, so a failed test is detected from its report and
    everything it recorded is discarded: a cassette with a half finished (or error) conversation must not survive.
    """
    handle = HfVcrTest(hf_vcr_session, _test_key(request))
    mark = len(hf_vcr_session.recorded)
    with hf_vcr_session.segment(f'{handle.test_key}') as segment:
        handle.main = segment
        yield handle
    if getattr(request.node, '_hf_vcr_failed', False):
        hf_vcr_session.discard(mark)

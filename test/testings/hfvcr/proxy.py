"""
Record and replay what a *subprocess* or a *native extension* says over HTTPS: ``git`` (and ``git-lfs``), ``hf_xet``.

VCR.py patches the Python HTTP libraries of the test process, so it cannot see ``git clone`` or the Rust client of Xet.
Both honour ``HTTPS_PROXY`` and a per-process CA bundle, so a proxy sees everything they say, without touching the system
trust store: this module runs ``mitmdump`` (mitmproxy) around a block of a test.

* the Python side of such a test stays with the cassettes of :mod:`.session`; only the traffic of the subprocess goes
  through the proxy (the Python clients are answered by their cassette before they reach it when replaying)
* flows are stored next to the cassettes (``<test>.git.mitm``), after :mod:`.mitm_scrub` removed credentials and e-mail addresses
* replay is **ordered** (a flow answers once; ``git push`` asks the same URL first without credentials, 401, then with them, 200),
  matches the ``Range`` header (``hf_xet`` reads three ranges of one URL in parallel) but not the request body (the objects of a
  ``git-lfs`` batch request come in a different order on every run), never connects to the real server
  (``connection_strategy=lazy``) and kills a request that was not recorded

``mitmdump`` is a separate program: mitmproxy needs a newer Python than the oldest the tests support, so it is found through
``$HFUTILS_MITMDUMP`` or ``PATH``. Behind a proxy of your own, set ``$HFUTILS_MITM_UPSTREAM`` to its URL while recording.
"""
import os
import shutil
import socket
import subprocess
import sys
import tempfile
import time
from contextlib import contextmanager
from typing import Iterator, List, Optional

MITMDUMP_ENV = 'HFUTILS_MITMDUMP'
UPSTREAM_ENV = 'HFUTILS_MITM_UPSTREAM'

_PROXY_VARS = ('HTTPS_PROXY', 'HTTP_PROXY', 'ALL_PROXY', 'https_proxy', 'http_proxy', 'all_proxy')
_TRUST_VARS = ('GIT_SSL_CAINFO', 'SSL_CERT_FILE', 'REQUESTS_CA_BUNDLE', 'CURL_CA_BUNDLE')
_OTHER_VARS = ('NO_PROXY', 'no_proxy', 'GIT_CONFIG_GLOBAL', 'GIT_CONFIG_SYSTEM', 'GIT_TERMINAL_PROMPT')

_SCRUB_ADDON = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'mitm_scrub.py')
_BLOCK_ADDON = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'mitm_block.py')


def find_mitmdump() -> Optional[str]:
    """Path of ``mitmdump``: ``$HFUTILS_MITMDUMP``, else ``PATH``."""
    configured = os.environ.get(MITMDUMP_ENV)
    if configured:
        return configured if os.path.exists(configured) else shutil.which(configured)
    return shutil.which('mitmdump')


def unavailable_reason() -> Optional[str]:
    """Why a test that needs the proxy cannot run here (``None`` when it can)."""
    if not sys.platform.startswith('linux'):
        return ('git based tests are only verified on Linux: git on Windows (schannel) and macOS may ignore '
                'GIT_SSL_CAINFO, so the proxy CA would not be trusted')
    if not find_mitmdump():
        return f'mitmdump (mitmproxy) is not installed, set ${MITMDUMP_ENV} or put it on PATH'
    if not shutil.which('git'):
        return 'git is not installed'
    try:
        ok = subprocess.run(['git', 'lfs', 'version'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).returncode == 0
    except OSError:
        ok = False
    if not ok:
        return 'git-lfs is not installed'
    return None


def _free_port() -> int:
    with socket.socket() as s:
        s.bind(('127.0.0.1', 0))
        return s.getsockname()[1]


def _wait_listening(port: int, process: 'subprocess.Popen', timeout: float = 60.0) -> None:
    deadline = time.time() + timeout
    while time.time() < deadline:
        if process.poll() is not None:
            raise RuntimeError(f'mitmdump exited with {process.returncode} before it listened')
        try:
            socket.create_connection(('127.0.0.1', port), timeout=0.5).close()
            return
        except OSError:
            time.sleep(0.2)
    raise RuntimeError('mitmdump did not start listening in time')


class ProxyHome:
    """A directory for everything the proxy and the isolated git configuration need during one test session."""

    def __init__(self):
        self.path = tempfile.mkdtemp(prefix='hfutils-test-mitm-')
        self.gitconfig = os.path.join(self.path, 'gitconfig')
        open(self.gitconfig, 'a').close()
        self._lfs_installed = False

    @property
    def ca_file(self) -> str:
        return os.path.join(self.path, 'mitmproxy-ca-cert.pem')

    def cleanup(self):
        if os.environ.get('HFUTILS_MITM_KEEP'):  # debugging: keep the proxy logs (record.log / replay.log)
            print(f'\nproxy home kept: {self.path}', file=sys.stderr)
            return
        shutil.rmtree(self.path, ignore_errors=True)

    def common_args(self) -> List[str]:
        return ['--set', f'confdir={self.path}', '--listen-host', '127.0.0.1']

    def ensure_lfs_filters(self, env: dict) -> None:
        """``git lfs install`` into the isolated global configuration, so that a clone smudges LFS files."""
        if not self._lfs_installed:
            subprocess.run(['git', 'lfs', 'install', '--skip-repo'], env=env, stdout=subprocess.DEVNULL,
                           stderr=subprocess.DEVNULL, check=False)
            self._lfs_installed = True


@contextmanager
def _python_clients_ignore_the_proxy() -> Iterator[None]:
    """
    The block routes subprocesses and native extensions through the proxy, not the Python clients of the test process: VCR
    answers those. ``huggingface_hub`` 1.x / 2.x (httpx) are patched below the point where a proxy matters; 0.x (``requests``)
    would show VCR the address of the proxy instead of huggingface.co, so its session ignores the environment inside the block.
    """
    try:
        import huggingface_hub
        from huggingface_hub import configure_http_backend
        from huggingface_hub.utils._http import _default_backend_factory
    except ImportError:
        yield
        return
    if hasattr(huggingface_hub, 'set_client_factory'):  # 1.x and 2.x have no configure_http_backend to speak of
        yield
        return

    def factory():
        session = _default_backend_factory()
        session.trust_env = False
        return session

    configure_http_backend(factory)
    try:
        yield
    finally:
        configure_http_backend()


@contextmanager
def _environment(home: ProxyHome, port: int) -> Iterator[dict]:
    """The proxy and the CA for every process started inside the block, git configuration isolated; restored after."""
    names = _PROXY_VARS + _TRUST_VARS + _OTHER_VARS
    saved = {k: os.environ.get(k) for k in names}
    try:
        for k in _PROXY_VARS:
            os.environ[k] = f'http://127.0.0.1:{port}'
        for k in _TRUST_VARS:
            os.environ[k] = home.ca_file
        os.environ['NO_PROXY'] = os.environ['no_proxy'] = ''
        os.environ['GIT_CONFIG_GLOBAL'] = home.gitconfig
        os.environ['GIT_CONFIG_SYSTEM'] = os.devnull
        os.environ['GIT_TERMINAL_PROMPT'] = '0'
        home.ensure_lfs_filters(dict(os.environ))
        with _python_clients_ignore_the_proxy():
            yield dict(os.environ)
    finally:
        for k, v in saved.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v


def _spawn(home: ProxyHome, args: List[str], log_path: str) -> 'tuple':
    port = _free_port()
    log = open(log_path, 'wb')
    process = subprocess.Popen([find_mitmdump(), '-p', str(port)] + home.common_args() + args,
                               stdout=log, stderr=subprocess.STDOUT)
    try:
        _wait_listening(port, process)
        deadline = time.time() + 30
        while not os.path.exists(home.ca_file) and time.time() < deadline:  # generated by the first start
            time.sleep(0.1)
    except BaseException:
        process.kill()
        raise
    return process, port, log


def _stop(process: 'subprocess.Popen', log) -> None:
    process.terminate()  # mitmdump flushes the file of ``-w`` on a graceful shutdown
    try:
        process.wait(timeout=30)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait()
    log.close()


def scrub(home: ProxyHome, raw: str, scrubbed: str) -> None:
    """Run the flows through :mod:`.mitm_scrub` (credentials, cookies, e-mail addresses removed)."""
    result = subprocess.run([find_mitmdump(), '-n', '-r', raw, '-s', _SCRUB_ADDON, '-w', scrubbed] + home.common_args(),
                            stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    if result.returncode != 0 or not os.path.exists(scrubbed):
        raise RuntimeError(f'scrubbing the recorded flows failed: {result.stdout.decode("utf-8", "replace")[-800:]}')


@contextmanager
def replaying(home: ProxyHome, flows: str) -> Iterator[None]:
    """Everything the processes of the block say over HTTPS is answered from ``flows``, nothing leaves the machine."""
    if os.path.exists(flows) and os.path.getsize(flows) > 0:
        args = ['--server-replay', flows, '--set', 'server_replay_extra=kill', '--set', 'server_replay_reuse=false',
                '--set', 'server_replay_use_headers=Range', '--set', 'server_replay_ignore_content=true']
    else:  # nothing recorded: refuse everything (mitmproxy would forward to the real server when it has no flow at all)
        args = ['-s', _BLOCK_ADDON]
    process, port, log = _spawn(home, args + ['--set', 'connection_strategy=lazy'], os.path.join(home.path, 'replay.log'))
    try:
        with _environment(home, port):
            yield
    finally:
        _stop(process, log)


@contextmanager
def recording(home: ProxyHome, flows: str, upstream: Optional[str] = None) -> Iterator[None]:
    """Everything the processes of the block say over HTTPS reaches the real server and is stored, scrubbed, in ``flows``."""
    upstream = upstream or os.environ.get(UPSTREAM_ENV)
    raw = os.path.join(home.path, 'raw.mitm')
    if os.path.exists(raw):
        os.remove(raw)
    args = ['-w', raw] + (['--mode', f'upstream:{upstream}'] if upstream else [])
    process, port, log = _spawn(home, args, os.path.join(home.path, 'record.log'))
    try:
        with _environment(home, port):
            yield
    finally:
        _stop(process, log)
    os.makedirs(os.path.dirname(flows), exist_ok=True)
    scrub(home, raw, flows)

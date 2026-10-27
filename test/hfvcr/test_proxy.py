"""Self tests of the proxy half of the framework (git, git-lfs and hf_xet are recorded through it). Local server only."""
import os
import subprocess
import sys
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import pytest

from test.testings.hfvcr import proxy

pytestmark = pytest.mark.skipif(proxy.find_mitmdump() is None, reason='mitmdump (mitmproxy) is not installed')


class _Handler(BaseHTTPRequestHandler):
    counter = 0

    def do_GET(self):
        type(self).counter += 1
        if self.path.startswith('/who'):
            body = b'{"name": "someone", "email": "someone@private.example", "token": "hf_' + b'a' * 34 + b'"}'
        else:
            body = f'answer {type(self).counter}'.encode()
        self.send_response(200)
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *args):
        pass


@pytest.fixture()
def server():
    _Handler.counter = 0
    httpd = ThreadingHTTPServer(('127.0.0.1', 0), _Handler)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    try:
        yield f'http://127.0.0.1:{httpd.server_address[1]}', httpd
    finally:
        httpd.shutdown()
        httpd.server_close()


@pytest.fixture()
def home():
    h = proxy.ProxyHome()
    try:
        yield h
    finally:
        h.cleanup()


_CLIENT = """
import os, sys, urllib.request
request = urllib.request.Request(sys.argv[1])
for pair in sys.argv[2:]:
    name, _, value = pair.partition('=')
    request.add_header(name, value)
opener = urllib.request.build_opener(urllib.request.ProxyHandler({'http': os.environ['HTTP_PROXY']}))
sys.stdout.write(opener.open(request, timeout=30).read().decode())
"""


def _get(url, headers=None):
    """Like git does it: a *subprocess* that finds the proxy in its environment (VCR only sees this process)."""
    args = [f'{k}={v}' for k, v in (headers or {}).items()]
    result = subprocess.run([sys.executable, '-c', _CLIENT, url] + args, env=os.environ.copy(),
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=120)
    if result.returncode != 0:
        raise ConnectionError(result.stderr.decode('utf-8', 'replace')[-300:])
    return result.stdout.decode()


@pytest.mark.unittest
class TestProxy:
    def test_record_then_replay_in_order_without_the_server(self, server, home, tmp_path):
        url, httpd = server
        flows = str(tmp_path / 'flows.mitm')
        with proxy.recording(home, flows):
            recorded = [_get(f'{url}/a'), _get(f'{url}/a'), _get(f'{url}/a')]
        assert recorded == ['answer 1', 'answer 2', 'answer 3']
        assert os.path.getsize(flows) > 0

        _Handler.counter = 100  # a live answer would now say 101
        with proxy.replaying(home, flows):
            assert [_get(f'{url}/a'), _get(f'{url}/a'), _get(f'{url}/a')] == recorded  # in order, once each

    def test_unrecorded_request_is_refused_and_never_reaches_the_server(self, server, home, tmp_path):
        url, httpd = server
        flows = str(tmp_path / 'flows.mitm')
        with proxy.recording(home, flows):
            _get(f'{url}/known')

        _Handler.counter = 100
        with proxy.replaying(home, flows):
            with pytest.raises(ConnectionError):
                _get(f'{url}/unknown')
        assert _Handler.counter == 100, 'the request reached the live server'

    def test_nothing_recorded_refuses_everything(self, server, home, tmp_path):
        url, httpd = server
        _Handler.counter = 100
        with proxy.replaying(home, str(tmp_path / 'does-not-exist.mitm')):
            with pytest.raises(ConnectionError):
                _get(f'{url}/a')
        assert _Handler.counter == 100

    def test_credentials_and_mail_are_scrubbed(self, server, home, tmp_path):
        url, httpd = server
        flows = str(tmp_path / 'flows.mitm')
        with proxy.recording(home, flows):
            body = _get(f'{url}/who', headers={'Authorization': 'Basic c2VjcmV0LXVzZXI6aGZfc2VjcmV0'})
        assert 'someone@private.example' in body  # the live answer is untouched
        data = open(flows, 'rb').read()
        assert b'Basic c2VjcmV0LXVzZXI6aGZfc2VjcmV0' not in data
        assert b'someone@private.example' not in data
        assert b'a' * 34 not in data
        assert b'redacted@example.invalid' in data

    def test_environment_is_restored(self, server, home, tmp_path):
        before = {k: os.environ.get(k) for k in ('HTTPS_PROXY', 'GIT_SSL_CAINFO', 'GIT_CONFIG_GLOBAL', 'NO_PROXY')}
        url, httpd = server
        with proxy.recording(home, str(tmp_path / 'flows.mitm')):
            assert os.environ['HTTPS_PROXY'].startswith('http://127.0.0.1:')
            assert os.environ['GIT_SSL_CAINFO'] == home.ca_file
            assert os.environ['GIT_CONFIG_GLOBAL'] == home.gitconfig
        assert {k: os.environ.get(k) for k in before} == before

    def test_failed_recording_keeps_no_flows(self, server, home, tmp_path):
        from test.testings.hfvcr import HfVcr
        session = HfVcr(str(tmp_path / 'cassettes'), mode='new')
        url, httpd = server
        try:
            session._proxy_home = home
            with pytest.raises(RuntimeError):
                with session.git_proxy('a/failing'):
                    _get(f'{url}/a')
                    raise RuntimeError('boom')
            assert not os.path.exists(os.path.splitext(session.path_of('a/failing'))[0] + '.mitm')
        finally:
            session._proxy_home = None

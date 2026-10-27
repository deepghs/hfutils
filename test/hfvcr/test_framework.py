"""Self tests of the cassette framework. They talk to a throw-away local server, never to Hugging Face."""
import json
import os
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import pytest
from huggingface_hub.utils import get_session

from test.testings.hfvcr import HfVcr, normalize_query, canonical_path, BlobJsonSerializer


class _Handler(BaseHTTPRequestHandler):
    counter = 0
    big = bytes(range(256)) * 64  # 16 KiB, not text

    def do_GET(self):
        if self.path.startswith('/count'):
            type(self).counter += 1
            body = str(type(self).counter).encode()
        elif self.path.startswith('/big'):
            body = self.big
        elif self.path.startswith('/whoami'):
            body = json.dumps({'name': 'someone', 'email': 'someone@private.example',
                               'token': 'hf_' + 'a' * 34}).encode()
        else:
            self.send_response(404)
            self.end_headers()
            return
        self.send_response(200)
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self):
        body = b'posted'
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
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    try:
        yield f'http://127.0.0.1:{httpd.server_address[1]}'
    finally:
        httpd.shutdown()
        httpd.server_close()


@pytest.fixture()
def session(tmp_path):
    return HfVcr(str(tmp_path / 'cassettes'), mode='new')


def _get(url):
    r = get_session().get(url, headers={'Authorization': 'Bearer hf_secret_that_must_not_be_stored'})
    return r.status_code, r.content


@pytest.mark.unittest
class TestFramework:
    def test_ordered_replay_of_stateful_endpoint(self, server, session):
        with session.segment('a/flow'):
            recorded = [_get(f'{server}/count')[1] for _ in range(3)]
        assert recorded == [b'1', b'2', b'3']

    def test_replay_without_server(self, server, session):
        with session.segment('a/flow'):
            recorded = [_get(f'{server}/count')[1] for _ in range(3)]
        _Handler.counter = 100  # a live server would now answer 101...

        replay = HfVcr(session.cassette_dir, mode='none')
        with replay.segment('a/flow'):
            assert [_get(f'{server}/count')[1] for _ in range(3)] == recorded

    def test_unrecorded_request_fails_in_none_mode(self, server, session):
        with session.segment('a/flow'):
            _get(f'{server}/count')
        replay = HfVcr(session.cassette_dir, mode='none')
        with replay.segment('a/flow'):
            _get(f'{server}/count')
            with pytest.raises(Exception) as ei:
                _get(f'{server}/big')  # never recorded, whatever was recorded for other paths
        assert 'CannotOverwriteExistingCassetteException' in repr(type(ei.value).__mro__)

    def test_missing_cassette_blocks_network(self, server, session):
        replay = HfVcr(session.cassette_dir, mode='none')
        with replay.segment('nothing/here'):
            with pytest.raises(Exception) as ei:
                _get(f'{server}/count')
        assert 'CannotOverwriteExistingCassetteException' in repr(type(ei.value).__mro__)

    def test_large_body_goes_to_blob_store(self, server, session):
        with session.segment('a/big'):
            code, data = _get(f'{server}/big')
        assert (code, data) == (200, _Handler.big)
        blobs = [os.path.join(d, f) for d, _, fs in os.walk(os.path.join(session.cassette_dir, '_blobs')) for f in fs]
        assert len(blobs) == 1
        with open(session.path_of('a/big')) as f:
            text = f.read()
        assert text.isascii() and len(text) < 4096

        replay = HfVcr(session.cassette_dir, mode='none')
        with replay.segment('a/big'):
            assert _get(f'{server}/big') == (200, _Handler.big)

    def test_secrets_are_scrubbed(self, server, session):
        with session.segment('a/who'):
            _get(f'{server}/whoami')
        with open(session.path_of('a/who')) as f:
            text = f.read()
        assert 'hf_secret_that_must_not_be_stored' not in text
        assert 'someone@private.example' not in text
        assert 'a' * 34 not in text
        assert 'redacted@example.invalid' in text

    def test_variables(self, session):
        calls = []

        def _factory():
            calls.append(1)
            return 'test_repo_xyz'

        with session.segment('a/vars') as seg:
            assert seg.var('repo', _factory) == 'test_repo_xyz'

        replay = HfVcr(session.cassette_dir, mode='none')
        with replay.segment('a/vars') as seg:
            assert seg.var('repo', _factory) == 'test_repo_xyz'
            with pytest.raises(KeyError):
                seg.var('other', _factory)
        assert len(calls) == 1

    def test_nested_segments_innermost_answers(self, server, session):
        with session.segment('outer'):
            outer = _get(f'{server}/count')[1]  # 1
            with session.segment('inner'):
                inner = _get(f'{server}/count')[1]  # 2
            after = _get(f'{server}/count')[1]  # 3
        assert (outer, inner, after) == (b'1', b'2', b'3')

        replay = HfVcr(session.cassette_dir, mode='none')
        with replay.segment('outer'):
            assert _get(f'{server}/count')[1] == b'1'
            with replay.segment('inner'):
                assert _get(f'{server}/count')[1] == b'2'
            assert _get(f'{server}/count')[1] == b'3'

    def test_failed_recording_keeps_nothing(self, server, session):
        with pytest.raises(RuntimeError):
            with session.segment('a/broken'):
                _get(f'{server}/count')
                raise RuntimeError('boom')
        assert not os.path.exists(session.path_of('a/broken'))

    def test_rewrite_replaces(self, server, session):
        with session.segment('a/flow'):
            _get(f'{server}/count')
        rewrite = HfVcr(session.cassette_dir, mode='rewrite')
        with rewrite.segment('a/flow'):
            assert _get(f'{server}/count')[1] == b'2'
        replay = HfVcr(session.cassette_dir, mode='none')
        with replay.segment('a/flow'):
            assert _get(f'{server}/count')[1] == b'2'

    def test_world_allows_repeats(self, server, session):
        with session.world('ref'):
            _get(f'{server}/count')
        replay = HfVcr(session.cassette_dir, mode='none')
        with replay.world('ref'):
            assert [_get(f'{server}/count')[1] for _ in range(4)] == [b'1'] * 4

    def test_normalize_query(self):
        assert normalize_query('https://x/a?recursive=False&expand=True') == normalize_query('https://x/a?recursive=false')
        assert normalize_query('https://x/a?b=1&a=2') == normalize_query('https://x/a?a=2&b=1')
        assert normalize_query('https://x/a?a=1') != normalize_query('https://x/a?a=2')

    def test_serializer_roundtrip_text_and_binary(self, tmp_path):
        s = BlobJsonSerializer(str(tmp_path / 'blobs'), inline_limit=8)
        data = {'version': 1, 'interactions': [{
            'request': {'method': 'GET', 'uri': 'http://x/', 'body': None, 'headers': {}},
            'response': {'status': {'code': 200, 'message': 'OK'}, 'headers': {}, 'body': {'string': b'\x00\x01' * 10}},
        }, {
            'request': {'method': 'POST', 'uri': 'http://x/', 'body': 'hi', 'headers': {}},
            'response': {'status': {'code': 200, 'message': 'OK'}, 'headers': {}, 'body': {'string': 'short'}},
        }]}
        out = s.deserialize(s.serialize(data))
        assert out['interactions'][0]['response']['body']['string'] == b'\x00\x01' * 10
        assert out['interactions'][1]['response']['body']['string'] == 'short'
        assert out['interactions'][1]['request']['body'] == 'hi'


@pytest.mark.unittest
class TestFailedTestsKeepNothing:
    def test_discard_removes_what_was_recorded_since_mark(self, server, session):
        with session.segment('keep/one'):
            _get(f'{server}/count')
        mark = len(session.recorded)
        with session.segment('drop/two') as seg:
            _get(f'{server}/count')
            seg.var('x', lambda: 1)
        assert os.path.exists(session.path_of('drop/two'))
        session.discard(mark)
        assert not os.path.exists(session.path_of('drop/two'))
        assert not os.path.exists(session.path_of('drop/two')[:-5] + '.vars.json')
        assert os.path.exists(session.path_of('keep/one'))


@pytest.mark.unittest
class TestClientGenerations:
    def test_resolve_cache_and_resolve_are_the_same_endpoint(self):
        assert canonical_path('/api/resolve-cache/datasets/a/b/abc123/dir%2Ffile.csv') == \
               ('/datasets/a/b/resolve/abc123/dir/file.csv', True)
        assert canonical_path('/api/resolve-cache/models/a/b/abc123/f.bin') == ('/a/b/resolve/abc123/f.bin', True)
        assert canonical_path('/datasets/a/b/resolve/abc123/dir/file.csv') == \
               ('/datasets/a/b/resolve/abc123/dir/file.csv', False)
        assert canonical_path('/api/datasets/a/b/tree/main/x%2Fy') == ('/api/datasets/a/b/tree/main/x/y', False)
        assert canonical_path('/api/datasets/a/b/tree/main/') == canonical_path('/api/datasets/a/b/tree/main')

    def test_presigned_url_signatures_are_ignored_but_upload_parts_are_not(self):
        a = 'https://us.gcp.cdn.hf.co/xet-bridge-us/abc/def?xip=1&user_id=public&X-Xet-Cas-Uid=public&Expires=1&Signature=x'
        b = 'https://us.gcp.cdn.hf.co/xet-bridge-us/abc/def?response-content-disposition=inline&Expires=2&Signature=y'
        assert normalize_query(a) == normalize_query(b) == []
        assert normalize_query('https://s3/x?partNumber=1&uploadId=u&X-Amz-Signature=s') == \
               [('partNumber', '1'), ('uploadId', 'u')]
        assert normalize_query('https://s3/x?partNumber=1&uploadId=u') != normalize_query('https://s3/x?partNumber=2&uploadId=u')

    def test_resolve_cache_query_is_ignored(self):
        assert normalize_query('https://x/api/resolve-cache/datasets/a/b/s/f?%2Fdatasets%2Fa%2Fb=&etag=1') == []

    def test_safe_requests_repeat_the_last_answer_once_exhausted(self, server, session):
        with session.segment('a/flow'):
            [_get(f'{server}/count') for _ in range(2)]  # 1, 2
        replay = HfVcr(session.cassette_dir, mode='none')
        with replay.segment('a/flow'):
            assert [_get(f'{server}/count')[1] for _ in range(5)] == [b'1', b'2', b'2', b'2', b'2']

    def test_unsafe_requests_never_repeat(self, server, session):
        with session.segment('a/post'):
            first = get_session().request('POST', f'{server}/count')
        assert first.status_code == 200

        replay = HfVcr(session.cassette_dir, mode='none')
        with replay.segment('a/post'):
            assert get_session().request('POST', f'{server}/count').status_code == 200
            with pytest.raises(Exception) as ei:  # one POST was recorded, a second one must not be answered
                get_session().request('POST', f'{server}/count')
        assert 'CannotOverwriteExistingCassetteException' in repr(type(ei.value).__mro__)


@pytest.mark.unittest
class TestContentAddressedUploads:
    @staticmethod
    def _request(oid, size):
        from vcr.request import Request
        body = json.dumps({'operation': 'upload', 'objects': [{'oid': oid, 'size': size}]}).encode()
        return Request('POST', 'https://huggingface.co/datasets/a/b.git/info/lfs/objects/batch', body, {})

    @staticmethod
    def _response(oid, size):
        body = json.dumps({'objects': [{'oid': oid, 'size': size, 'actions': {'upload': {'href': f'https://s3/{oid}'}}}]})
        return {'status': {'code': 200, 'message': 'OK'}, 'headers': {'content-length': [str(len(body))]},
                'body': {'string': body.encode()}}

    def test_batch_answer_follows_the_asked_object(self):
        from test.testings.hfvcr.replay import adapt_lfs_batch
        recorded = self._response('a' * 64, 10)
        out = adapt_lfs_batch(self._request('b' * 64, 99), recorded)
        answer = json.loads(out['body']['string'])['objects'][0]
        assert (answer['oid'], answer['size']) == ('b' * 64, 99)
        assert answer['actions']['upload']['href'] == f'https://s3/{"a" * 64}'  # recorded URLs stay
        assert out['headers']['content-length'] == [str(len(out['body']['string']))]
        assert json.loads(recorded['body']['string'])['objects'][0]['oid'] == 'a' * 64  # the cassette is untouched

    def test_other_requests_are_left_alone(self):
        from vcr.request import Request
        from test.testings.hfvcr.replay import adapt_lfs_batch
        response = self._response('a' * 64, 10)
        assert adapt_lfs_batch(Request('GET', 'https://huggingface.co/api/x', None, {}), response) is response


@pytest.mark.unittest
class TestThreads:
    """``hfutils`` downloads and warms up in parallel; replay must hold under threads on every vcrpy and client."""

    def test_parallel_replay_never_reaches_the_real_server(self, server, session):
        workers, per_worker = 8, 6
        with session.segment('a/threads'):
            recorded = [_get(f'{server}/count')[1] for _ in range(workers * per_worker)]
        assert len(set(recorded)) == workers * per_worker

        for _ in range(3):  # the races are not deterministic
            _Handler.counter = 10_000  # any request that gets to the live server moves this
            replay = HfVcr(session.cassette_dir, mode='none')
            seen, errors = [], []

            def _work():
                try:
                    for _ in range(per_worker):
                        seen.append(_get(f'{server}/count')[1])
                except Exception as e:  # noqa
                    errors.append(repr(e))

            with replay.segment('a/threads'):
                threads = [threading.Thread(target=_work) for _ in range(workers)]
                for t in threads:
                    t.start()
                for t in threads:
                    t.join()

            assert not errors, errors[:2]
            assert _Handler.counter == 10_000, 'a request skipped the cassette and reached the server'
            assert sorted(seen) == sorted(recorded)


@pytest.mark.unittest
class TestVariants:
    def test_variant_answers_only_when_it_exists(self, server, session, tmp_path):
        with session.segment('a/flow'):
            _get(f'{server}/count')  # default: 1
        recording = HfVcr(session.cassette_dir, mode='new', record_variant='hub0')
        with recording.segment('a/flow'):
            _get(f'{server}/count')  # variant: 2
        assert os.path.exists(session.path_of('a/flow')) and os.path.exists(recording.path_of('a/flow'))
        assert session.path_of('a/flow') != recording.path_of('a/flow')

        with HfVcr(session.cassette_dir, mode='none', variant='hub0').segment('a/flow'):
            assert _get(f'{server}/count')[1] == b'2'
        with HfVcr(session.cassette_dir, mode='none', variant='other').segment('a/flow'):
            assert _get(f'{server}/count')[1] == b'1'
        with HfVcr(session.cassette_dir, mode='none').segment('a/flow'):
            assert _get(f'{server}/count')[1] == b'1'


@pytest.mark.unittest
def test_serializer_accepts_chunked_request_bodies(tmp_path):
    s = BlobJsonSerializer(str(tmp_path / 'blobs'), inline_limit=4)
    data = {'version': 1, 'interactions': [{
        'request': {'method': 'PUT', 'uri': 'http://x/', 'body': [b'ab', b'cd', 'ef', bytearray(b'gh')], 'headers': {}},
        'response': {'status': {'code': 200, 'message': 'OK'}, 'headers': {}, 'body': {'string': b''}},
    }]}
    out = s.deserialize(s.serialize(data))
    assert out['interactions'][0]['request']['body'] == b'abcdefgh'

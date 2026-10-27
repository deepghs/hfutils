"""
Replay policy for requests that were made more often than they were recorded.

VCR.py plays every recorded response once. Client generations do not agree on how many safe requests they send
(``huggingface_hub`` 1.x repeats a ``HEAD`` that 2.x sends once), and a test must not fail only because of that.
Once every recorded answer of a ``GET`` / ``HEAD`` has been played, further identical requests get the **last**
recorded answer, which is the most recent state of the resource. Anything that changes state (``POST``, ``PUT``,
``DELETE``, ...) stays strictly one answer per recorded request, in order.
"""
import copy
import json
import threading

from vcr.cassette import Cassette
from vcr.errors import UnhandledHTTPRequestError

SAFE_METHODS = frozenset({'GET', 'HEAD'})

_PLAY_LOCK = threading.RLock()

_original_contains = Cassette.__contains__
_original_play_response = Cassette.play_response


def _last_match(cassette, request):
    last = None
    for index, response in cassette._responses(request):
        last = (index, response)
    return last


def adapt_lfs_batch(request, response):
    """
    Answer an LFS batch request for the objects it asks about, not for the ones that were asked at recording time.

    The batch endpoint is content addressed: it answers per ``oid`` (sha256) and ``size`` of the uploaded bytes. A test
    that uploads something built on the spot (a zip carries file times, and zlib builds differ between platforms) asks
    about other oids than the recording did. The recorded answer is reused with the oids and sizes of the live request,
    in order; the upload and verify URLs stay as recorded and are matched as recorded.
    """
    if request.method != 'POST' or not request.path.endswith('/info/lfs/objects/batch'):
        return response
    try:
        asked = json.loads(request.body)['objects']
        body = json.loads(response['body']['string'])
        recorded = body['objects']
    except (ValueError, KeyError, TypeError):
        return response
    if len(asked) != len(recorded):
        return response
    adapted = copy.deepcopy(response)
    for ask, answer in zip(asked, body['objects']):
        answer['oid'], answer['size'] = ask['oid'], ask['size']
    data = json.dumps(body).encode('utf-8')
    adapted['body'] = {'string': data}
    for name in list(adapted.get('headers', {})):
        if name.lower() == 'content-length':
            adapted['headers'][name] = [str(len(data))]
    return adapted


def _contains(self, request):
    if _original_contains(self, request):
        return True
    return bool(getattr(self, 'hf_safe_repeats', False) and request.method in SAFE_METHODS
                and _last_match(self, request) is not None)


def _play_response(self, request):
    # "is this answer unplayed?" and "it is played now" are two steps in vcrpy: two threads asking for the same URL could both
    # take the same recorded answer and leave another one unplayed. One lock makes the pair atomic.
    with _PLAY_LOCK:
        return _play_response_locked(self, request)


def _play_response_locked(self, request):
    try:
        response = _original_play_response(self, request)
    except UnhandledHTTPRequestError:
        if getattr(self, 'hf_safe_repeats', False) and request.method in SAFE_METHODS:
            found = _last_match(self, request)
            if found is not None:
                self.play_counts[found[0]] += 1
                return adapt_lfs_batch(request, found[1])
        raise
    return adapt_lfs_batch(request, response) if getattr(self, 'hf_safe_repeats', False) else response


Cassette.__contains__ = _contains
Cassette.play_response = _play_response


def enable_safe_repeats(cassette: Cassette) -> None:
    """Switch the policy on for one cassette (it is a no-op for every cassette that is not switched on)."""
    cassette.hf_safe_repeats = True


def _patch_httpx_binary_request_bodies() -> None:
    """
    vcrpy 7.x (the newest that supports Python 3.9) reads an httpx request body with ``.decode("utf-8")``, which
    raises for the binary body of an upload. Keep such bodies as bytes. Newer vcrpy does not need this and is left alone.
    """
    try:
        from vcr.stubs import httpx_stubs
        import inspect
        source = inspect.getsource(httpx_stubs._make_vcr_request)
    except (ImportError, AttributeError, OSError, TypeError):
        return
    if '.decode("utf-8")' not in source:
        return

    def _make_vcr_request(httpx_request, **kwargs):
        body = httpx_request.read()
        try:
            body = body.decode('utf-8')
        except UnicodeDecodeError:
            pass
        return httpx_stubs.VcrRequest(httpx_request.method, str(httpx_request.url), body, dict(httpx_request.headers))

    httpx_stubs._make_vcr_request = _make_vcr_request


_patch_httpx_binary_request_bodies()


def _patch_httpx_threadsafe_playback() -> None:
    """
    vcrpy 7.0 builds every played httpx response under ``@patch("httpx.Response.read", MagicMock())`` and
    ``@patch("httpx.Response.close", ...)``, which swap *global* attributes for the duration of the call. Under threads
    (``hfutils`` downloads and warms up in parallel) that races two ways: one ``_patch`` object entered by two threads
    fails with ``AttributeError: '_patch' object has no attribute 'is_local'``, and a thread that calls the real
    ``response.read()`` meanwhile gets a mock and never loads the body (``httpx.ResponseNotRead``).

    The same response is built here without touching global state: ``httpx.Response.__init__`` calls ``read()`` on
    in-memory content, so a throw-away subclass makes that call (and ``close``) a no-op and the instance gets its real
    class back right after. vcrpy 8 and newer do not patch and are left alone.
    """
    try:
        import httpx
        from vcr.stubs import httpx_stubs
        original = httpx_stubs._from_serialized_response
    except (ImportError, AttributeError):
        return
    if not hasattr(original, 'patchings'):  # not decorated with mock.patch: nothing to fix
        return

    class _QuietResponse(httpx.Response):
        def read(self):
            return b''

        def close(self):
            pass

    def _from_serialized_response(request, serialized_response, history=None):
        if 'status_code' in serialized_response:  # cassette format of old vcrpy versions
            serialized_response = httpx_stubs.decode_response(httpx_stubs.convert_body_to_bytes({
                'headers': serialized_response['headers'],
                'body': {'string': serialized_response['content']},
                'status': {'code': serialized_response['status_code']},
            }))
            extensions = None
        else:
            extensions = {'reason_phrase': serialized_response['status']['message'].encode()}
        response = _QuietResponse(
            status_code=serialized_response['status']['code'],
            request=request,
            headers=httpx_stubs._from_serialized_headers(serialized_response['headers']),
            content=serialized_response['body']['string'],
            history=history or [],
            extensions=extensions,
        )
        response.__class__ = httpx.Response
        return response

    httpx_stubs._from_serialized_response = _from_serialized_response


_patch_httpx_threadsafe_playback()


def reset_http_sessions() -> None:
    """
    Drop every pooled HTTP connection of ``huggingface_hub``.

    A keep-alive connection built while one cassette was active would otherwise be reused under the next one and answer
    from the wrong cassette (or fail inside VCR's connection stub); vcrpy fixed that only in 8.3, and the older vcrpy is all
    that Python 3.8 / 3.9 can install. ``reset_sessions`` is the name in 0.x, ``close_session`` in 1.x and 2.x.
    """
    try:
        from huggingface_hub import utils as hf_utils
    except ImportError:
        return
    for name in ('reset_sessions', 'close_session'):
        func = getattr(hf_utils, name, None)
        if func is not None:
            try:
                func()
            except Exception:  # a session that cannot be closed is not worth failing a test for
                pass
            return


def _patch_threadsafe_force_reset() -> None:
    """
    vcrpy up to 7.x builds every connection stub under ``vcr.patch.force_reset()``, which swaps ``http.client``'s classes
    back to the real ones with ``mock.patch.object`` for a moment. Those patches are global and their enter / exit must nest.
    With threads they interleave (A enters, B enters and saves the *real* class as the one to restore, A leaves, B leaves),
    which restores the real class for good: from then on every thread opens real connections, past the cassette.

    A reentrant lock makes the swaps nest. It is a no-op for versions that do not have the function.
    """
    try:
        import vcr.patch as vcr_patch
        original = vcr_patch.force_reset
    except (ImportError, AttributeError):
        return
    if getattr(original, 'hf_locked', False):
        return
    import contextlib
    import threading
    lock = threading.RLock()

    @contextlib.contextmanager
    def force_reset():
        with lock, original():
            yield

    force_reset.hf_locked = True
    vcr_patch.force_reset = force_reset  # the stubs import it by name at call time

    # A pool that opens a connection while another thread is inside ``force_reset`` reads the *real* ``ConnectionCls``.
    # Opening happens under the same lock, so it waits for the swap to be over.
    for module_name in ('urllib3.connectionpool', 'requests.packages.urllib3.connectionpool'):
        try:
            module = __import__(module_name, fromlist=['HTTPConnectionPool'])
        except ImportError:
            continue
        for pool_class in (module.HTTPConnectionPool, module.HTTPSConnectionPool):
            new_conn = pool_class._new_conn
            if getattr(new_conn, 'hf_locked', False):
                continue

            def _make(new_conn):
                def _new_conn(self, *args, **kwargs):
                    with lock:
                        return new_conn(self, *args, **kwargs)
                _new_conn.hf_locked = True
                return _new_conn

            pool_class._new_conn = _make(new_conn)


_patch_threadsafe_force_reset()

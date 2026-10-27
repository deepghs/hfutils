"""
Matching and scrubbing rules shared by recording and replay.

*Matching* decides whether a request made during replay is "the same" as a recorded one. It is tuned so
that **one recording replays on every supported client**: ``huggingface_hub`` 0.x (requests), 1.x (httpx)
and 2.x (httpx2) differ in how they spell query strings (``recursive=False`` vs ``recursive=false``) and
in optional parameters (``expand``), but the server answers the same.

*Scrubbing* removes credentials and personal data before anything is written to a cassette.
"""
import re
from urllib.parse import urlparse, parse_qsl, unquote

from . import redact

#: Query parameters that only change how much the server answers, never which resource it is.
IGNORED_QUERY_PARAMS = frozenset({'expand'})

#: Parameters of pre-signed CDN / storage URLs that change with every signature, not with the resource. Parameters that pick a
#: part of an upload (``partNumber``, ``uploadId``) are deliberately not in this list.
VOLATILE_QUERY_PARAMS = frozenset({'xip', 'user_id', 'expires', 'signature', 'key-pair-id', 'policy', 'x-id',
                                   'response-content-disposition', 'response-content-type'})
VOLATILE_QUERY_PREFIXES = ('x-amz-', 'x-xet-')

#: Request / response headers never written to a cassette (one list for VCR cassettes and mitmproxy flows).
FILTERED_REQUEST_HEADERS = redact.REQUEST_HEADERS
FILTERED_RESPONSE_HEADERS = redact.RESPONSE_HEADERS

#: ``huggingface_hub`` 1.x downloads a file of a pinned commit from ``/api/resolve-cache/<type>s/<repo>/<sha>/<file>``,
#: 2.x reaches the very same endpoint through ``/<type>s/<repo>/resolve/<sha>/<file>``.
_RESOLVE_CACHE = re.compile(r'^/api/resolve-cache/(?:(?P<type>datasets|spaces|models)/)?'
                            r'(?P<repo>[^/]+/[^/]+)/(?P<rev>[^/]+)/(?P<file>.+)$')


def canonical_path(path: str):
    """
    Canonical form of the path of an URI, and whether it was a ``resolve-cache`` one.

    Slashes inside a path segment may be spelled ``%2F`` or ``/`` depending on the client, so the path is unquoted,
    and a trailing slash (``.../tree/main/``) means nothing.
    """
    path = unquote(path)
    if len(path) > 1:
        path = path.rstrip('/')
    m = _RESOLVE_CACHE.match(path)
    if m:
        prefix = '' if m.group('type') in (None, 'models') else f'/{m.group("type")}'
        return f'{prefix}/{m.group("repo")}/resolve/{m.group("rev")}/{m.group("file")}', True
    return path, False


def normalize_query(uri: str):
    """
    Canonical form of the query string of an URI: sorted, lowercase booleans, volatile parameters dropped.

    The query of a ``resolve-cache`` URI only echoes its own path, so it is dropped altogether.
    """
    parsed = urlparse(uri)
    if canonical_path(parsed.path)[1]:
        return []
    items = []
    for key, value in parse_qsl(parsed.query, keep_blank_values=True):
        lowered = key.lower()
        if key in IGNORED_QUERY_PARAMS or lowered in VOLATILE_QUERY_PARAMS or lowered.startswith(VOLATILE_QUERY_PREFIXES):
            continue
        items.append((key, value.lower() if value.lower() in ('true', 'false') else value))
    return sorted(items)


def match_path(r1, r2):
    """VCR.py matcher: equal after :func:`canonical_path`."""
    p1, p2 = canonical_path(urlparse(r1.uri).path)[0], canonical_path(urlparse(r2.uri).path)[0]
    assert p1 == p2, f'path differs: {p1!r} != {p2!r}'


def match_query(r1, r2):
    """VCR.py matcher: equal after :func:`normalize_query`."""
    q1, q2 = normalize_query(r1.uri), normalize_query(r2.uri)
    assert q1 == q2, f'query differs: {q1!r} != {q2!r}'


def scrub_request(request):
    """VCR.py ``before_record_request`` hook, also applied to the live request that is looked up while replaying."""
    request.uri = redact.redact_str(request.uri)
    return request


def scrub_response(response: dict) -> dict:
    """VCR.py ``before_record_response`` hook: credentials, signatures, cookies and e-mail addresses never reach a cassette."""
    headers = response.get('headers') or {}
    for name in list(headers):
        if name.lower() in FILTERED_RESPONSE_HEADERS:
            del headers[name]
        else:
            headers[name] = redact.header_values(name, headers[name])
    body = response.get('body') or {}
    data = body.get('string')
    if isinstance(data, bytes) and len(data) < 1 << 22:
        new = redact.redact_bytes(data)
        if new != data:
            body['string'] = new
            for name in list(headers):
                if name.lower() == 'content-length':
                    headers[name] = [str(len(new))]
    return response

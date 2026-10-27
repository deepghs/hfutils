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

#: Query parameters that only change how much the server answers, never which resource it is.
IGNORED_QUERY_PARAMS = frozenset({'expand'})

#: Parameters of pre-signed CDN / storage URLs that change with every signature, not with the resource. Parameters that pick a
#: part of an upload (``partNumber``, ``uploadId``) are deliberately not in this list.
VOLATILE_QUERY_PARAMS = frozenset({'xip', 'user_id', 'expires', 'signature', 'key-pair-id', 'policy', 'x-id',
                                   'response-content-disposition', 'response-content-type'})
VOLATILE_QUERY_PREFIXES = ('x-amz-', 'x-xet-')

#: Request headers never written to a cassette.
FILTERED_REQUEST_HEADERS = ('authorization', 'cookie', 'user-agent', 'x-hf-user-agent', 'x-amz-security-token')

#: Response headers never written to a cassette.
FILTERED_RESPONSE_HEADERS = ('set-cookie', 'x-request-id', 'x-amz-cf-id', 'x-amz-request-id', 'x-amz-id-2',
                             'x-amz-server-side-encryption-aws-kms-key-id', 'cf-ray', 'via', 'date', 'x-cache',
                             'x-amz-cf-pop', 'age')

_EMAIL_PATTERN = re.compile(rb'("email"\s*:\s*")[^"]*(")')
_HF_TOKEN_PATTERN = re.compile(rb'hf_[A-Za-z0-9]{30,}')


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


def scrub_response(response: dict) -> dict:
    """VCR.py ``before_record_response`` hook."""
    headers = response.get('headers') or {}
    for name in list(headers):
        if name.lower() in FILTERED_RESPONSE_HEADERS:
            del headers[name]
    body = response.get('body') or {}
    data = body.get('string')
    if isinstance(data, bytes) and len(data) < 1 << 20 and (b'"email"' in data or b'hf_' in data):
        data = _EMAIL_PATTERN.sub(rb'\1redacted@example.invalid\2', data)
        data = _HF_TOKEN_PATTERN.sub(b'hf_REDACTED', data)
        body['string'] = data
        for name in list(headers):
            if name.lower() == 'content-length':
                headers[name] = [str(len(data))]
    return response

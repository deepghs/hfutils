"""
What may never be written into a cassette or a recorded flow, in one place.

This module uses the standard library only and imports nothing from its package: ``mitm_scrub.py`` runs inside the
interpreter of the mitmproxy installation and loads it by path, ``scrub.py`` (VCR cassettes), ``maintenance.py`` (re-scrubbing
what is already committed) and the guard test ``test/hfvcr/test_cassettes_clean.py`` import it as a module.

Consistency matters as much as secrecy: a pre-signed URL is *recorded* in a ``Location`` header or in a JSON body and
*requested* afterwards by the client, and replay finds the request by its URL. The same substitution is therefore applied to
the URL of every request, to every header value and to every text body, so both sides stay equal after redaction.
"""
import re
from typing import List

REDACTED = 'REDACTED'

#: Request headers that are never stored.
REQUEST_HEADERS = ('authorization', 'cookie', 'user-agent', 'x-hf-user-agent', 'x-amz-security-token',
                   'x-xet-access-token')

#: Headers that must stay (the client refuses to start without them) but whose value is replaced.
#: ``huggingface_hub`` needs ``X-Xet-Access-Token`` in the answer of ``resolve`` to hand a download over to ``hf_xet`` (the value
#: is a credential), and ``hf_xet`` compares ``X-Xet-Token-Expiration`` with the clock to decide whether it has to ask for a new
#: token: a recorded timestamp would make every replay after that moment fail, so it becomes a date far in the future.
MASKED_HEADERS = {'x-xet-access-token': 'REDACTED', 'x-xet-token-expiration': '4102444800'}

#: Response headers that are never stored.
RESPONSE_HEADERS = ('set-cookie', 'x-request-id', 'x-amz-cf-id', 'x-amz-request-id', 'x-amz-id-2', 'x-amz-cf-pop',
                    'x-amz-server-side-encryption-aws-kms-key-id', 'cf-ray', 'via', 'date', 'x-cache', 'age',
                    'x-amz-security-token')

#: Query parameters of a pre-signed URL that carry a credential, a signature or a client address. The others
#: (``Expires``, ``X-Xet-Cas-Uid``, ``partNumber``, ...) say nothing secret and some of them pick a part of an upload.
SENSITIVE_PARAMS = ('Signature', 'X-Amz-Signature', 'X-Amz-Security-Token', 'X-Amz-Credential', 'Key-Pair-Id', 'Policy',
                    'xip', 'X-Xet-Signature', 'user_id', 'X-Xet-Session-Id')

# a parameter follows ``?``, ``&``, or the JSON escape of ``&`` that some encoders write (``&``) or HTML (``&amp;``)
_SEP = r'(?:[?&]|\\u0026|&amp;)'
_NAMES = '|'.join(re.escape(p) for p in SENSITIVE_PARAMS)
_VALUE = r'''[^&"'\\\s<>;]+'''
_PARAM = re.compile(f'({_SEP})({_NAMES})=({_VALUE})', re.I)
_PARAM_B = re.compile(_PARAM.pattern.encode(), re.I)

_JWT = re.compile(r'eyJ[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}')
_JWT_B = re.compile(_JWT.pattern.encode())
_HF_TOKEN = re.compile(r'hf_(?!REDACTED)[A-Za-z0-9]{30,}')
_HF_TOKEN_B = re.compile(_HF_TOKEN.pattern.encode())
_EMAIL_B = re.compile(rb'("email"\s*:\s*")[^"]*(")')
_AUTH_JSON_B = re.compile(rb'("Authorization"\s*:\s*")[^"]*(")', re.I)
_ACCESS_TOKEN_B = re.compile(rb'("(?:accessToken|access_token)"\s*:\s*")[^"]+(")')

#: The e-mail address written in place of a real one.
EMAIL_PLACEHOLDER = 'redacted@example.invalid'


def header_values(name: str, values: List[str]) -> List[str]:
    """The values of one header that is kept: masked when it is a credential, redacted otherwise."""
    if name.lower() in MASKED_HEADERS:
        return [MASKED_HEADERS[name.lower()] for _ in values]
    return [redact_str(v) for v in values]


def redact_str(text: str) -> str:
    """Redact an URL or a header value."""
    text = _PARAM.sub(lambda m: f'{m.group(1)}{m.group(2)}={REDACTED}', text)
    text = _JWT.sub('JWT_REDACTED', text)
    return _HF_TOKEN.sub('hf_REDACTED', text)


def redact_bytes(data: bytes) -> bytes:
    """Redact a body. Text only: anything that is evidently binary (an archive, an image) is returned untouched."""
    if b'\x00' in data[:2048]:
        return data
    data = _PARAM_B.sub(lambda m: m.group(1) + m.group(2) + b'=' + REDACTED.encode(), data)
    data = _JWT_B.sub(b'JWT_REDACTED', data)
    data = _HF_TOKEN_B.sub(b'hf_REDACTED', data)
    data = _EMAIL_B.sub(rb'\1' + EMAIL_PLACEHOLDER.encode() + rb'\2', data)
    data = _AUTH_JSON_B.sub(rb'\1' + REDACTED.encode() + rb'\2', data)
    return _ACCESS_TOKEN_B.sub(rb'\1' + REDACTED.encode() + rb'\2', data)


def violations(data: bytes) -> List[str]:
    """Names of the secrets that are still in ``data`` (empty list: clean). The guard test runs this on every artifact."""
    found = []
    for m in _PARAM_B.finditer(data):
        if m.group(3).decode('latin-1') != REDACTED:
            found.append(f'unredacted {m.group(2).decode("latin-1")}=')
    if _JWT_B.search(data):
        found.append('JWT')
    if _HF_TOKEN_B.search(data):
        found.append('hf_ token')
    for m in _EMAIL_B.finditer(data):
        if EMAIL_PLACEHOLDER.encode() not in m.group(0):
            found.append('e-mail address')
    for m in _AUTH_JSON_B.finditer(data):
        if REDACTED.encode() not in m.group(0):
            found.append('Authorization value in JSON')
    for m in _ACCESS_TOKEN_B.finditer(data):
        if REDACTED.encode() not in m.group(0):
            found.append('accessToken value')
    return sorted(set(found))

"""
mitmproxy add-on that removes credentials and personal data from recorded flows.

It is run by :mod:`.proxy` as ``mitmdump -n -r raw.mitm -s mitm_scrub.py -w scrubbed.mitm``: mitmproxy feeds every
stored flow through the add-ons' ``request`` / ``response`` hooks and writes what is left. This file must only import
``mitmproxy`` and the standard library, it runs in the interpreter of the mitmproxy installation, not in the one of the tests.
"""
import re

_REQUEST_HEADERS = ('authorization', 'cookie', 'user-agent', 'x-hf-user-agent')
_RESPONSE_HEADERS = ('set-cookie', 'x-request-id', 'x-amz-cf-id', 'x-amz-request-id', 'x-amz-id-2', 'cf-ray')
_EMAIL = re.compile(rb'("email"\s*:\s*")[^"]*(")')
_TOKEN = re.compile(rb'hf_[A-Za-z0-9]{30,}')


def _drop(headers, names):
    for name in names:
        while name in headers:
            del headers[name]


class Scrub:
    def request(self, flow):
        _drop(flow.request.headers, _REQUEST_HEADERS)

    def response(self, flow):
        _drop(flow.response.headers, _RESPONSE_HEADERS)
        body = flow.response.content
        if body and len(body) < (1 << 20) and (b'email' in body or b'hf_' in body):
            new = _TOKEN.sub(b'hf_REDACTED', _EMAIL.sub(rb'\1redacted@example.invalid\2', body))
            if new != body:
                flow.response.content = new


addons = [Scrub()]

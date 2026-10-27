"""
mitmproxy add-on that removes credentials, signatures and personal data from recorded flows.

It is run by :mod:`.proxy` as ``mitmdump -n -r raw.mitm -s mitm_scrub.py -w scrubbed.mitm`` (and by :mod:`.maintenance` on flows
that are already committed): mitmproxy feeds every stored flow through the add-ons' ``request`` / ``response`` hooks and writes
what is left. This file runs in the interpreter of the mitmproxy installation, not in the one of the tests, so it only imports
``mitmproxy`` and the standard library; the rules live in ``redact.py``, which is loaded by path so that cassettes and flows
are scrubbed by the very same code.
"""
import importlib.util
import os

_spec = importlib.util.spec_from_file_location('hfvcr_redact', os.path.join(os.path.dirname(os.path.abspath(__file__)), 'redact.py'))
redact = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(redact)


def _drop(headers, names):
    for name in names:
        while name in headers:
            del headers[name]


def _redact_values(headers):
    for name in list(headers.keys()):
        values = headers.get_all(name)
        new = redact.header_values(name, values)
        if new != values:
            headers.set_all(name, new)


class Scrub:
    def request(self, flow):
        _drop(flow.request.headers, redact.REQUEST_HEADERS)
        _redact_values(flow.request.headers)
        flow.request.path = redact.redact_str(flow.request.path)  # the path carries the query string of a pre-signed URL

    def response(self, flow):
        _drop(flow.response.headers, redact.RESPONSE_HEADERS)
        _redact_values(flow.response.headers)
        body = flow.response.content
        if body and len(body) < (1 << 22):
            new = redact.redact_bytes(body)
            if new != body:
                flow.response.content = new  # also updates Content-Length


addons = [Scrub()]

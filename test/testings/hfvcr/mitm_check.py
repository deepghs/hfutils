"""
mitmproxy add-on that *reports* what a stored flow still contains that must not be there (used by the guard test).

``mitmdump -n -r flows.mitm -s mitm_check.py`` prints one ``LEAK <what>`` line per problem and nothing when the flows are clean.
Like ``mitm_scrub.py`` it runs in the interpreter of the mitmproxy installation and loads ``redact.py`` by path.
"""
import importlib.util
import os

_spec = importlib.util.spec_from_file_location('hfvcr_redact', os.path.join(os.path.dirname(os.path.abspath(__file__)), 'redact.py'))
redact = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(redact)


def _headers_blob(headers):
    return '\n'.join(f'{k}: {v}' for k, v in headers.items(True)).encode('utf-8', 'replace')


class HfvcrCheck:
    def request(self, flow):
        for name in redact.REQUEST_HEADERS:
            if name in flow.request.headers:
                print(f'LEAK request header {name}', flush=True)
        for problem in redact.violations(flow.request.url.encode('utf-8', 'replace') + b'\n' + _headers_blob(flow.request.headers)
                                         + b'\n' + (flow.request.content or b'')):
            print(f'LEAK request {problem}', flush=True)

    def response(self, flow):
        for name in redact.RESPONSE_HEADERS:
            if name in flow.response.headers:
                print(f'LEAK response header {name}', flush=True)
        for name, masked in redact.MASKED_HEADERS.items():
            if name in flow.response.headers and flow.response.headers[name] != masked:
                print(f'LEAK response header {name} holds a value', flush=True)
        for problem in redact.violations(_headers_blob(flow.response.headers) + b'\n' + (flow.response.content or b'')):
            print(f'LEAK response {problem}', flush=True)


addons = [HfvcrCheck()]

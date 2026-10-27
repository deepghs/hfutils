"""
Guard: nothing that must not be committed is in a recorded cassette, blob or flow.

Fails with the list of the files and what is left in them. Fix by running
``python -m test.testings.hfvcr.maintenance`` (re-scrubs with the current rules) and, when the rules are too weak,
by extending ``test/testings/hfvcr/redact.py`` first.
"""
import glob
import json
import os

import pytest

from test.testings.hfvcr import proxy, redact
from test.testings.hfvcr import maintenance
from test.testings.hfvcr.serializer import BlobJsonSerializer

CASSETTES = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'cassettes')


def _text(body):
    if body is None:
        return b''
    return body.encode('utf-8') if isinstance(body, str) else bytes(body)


@pytest.mark.unittest
class TestRecordedArtifactsAreClean:
    def test_cassettes(self):
        serializer = BlobJsonSerializer(os.path.join(CASSETTES, '_blobs'))
        leaks = {}
        for path in sorted(glob.glob(os.path.join(CASSETTES, '**', '*.json'), recursive=True)):
            if path.endswith('.vars.json'):
                continue
            with open(path, 'r') as f:
                data = serializer.deserialize(f.read())
            found = set()
            for item in data['interactions']:
                request, response = item['request'], item['response']
                blob = request['uri'].encode() + b'\n'
                for headers, names in ((request.get('headers') or {}, redact.REQUEST_HEADERS),
                                       (response.get('headers') or {}, redact.RESPONSE_HEADERS)):
                    for name, values in headers.items():
                        if name.lower() in names:
                            found.add(f'header {name}')
                        if name.lower() in redact.MASKED_HEADERS and list(values) != [redact.MASKED_HEADERS[name.lower()]]:
                            found.add(f'header {name} holds a value')
                        blob += f'{name}: {values}\n'.encode('utf-8', 'replace')
                blob += _text(request['body']) + b'\n' + _text(response['body']['string'])
                found.update(redact.violations(blob))
            if found:
                leaks[os.path.relpath(path, CASSETTES)] = sorted(found)
        assert not leaks, f'secrets in cassettes, run python -m test.testings.hfvcr.maintenance: {leaks}'

    def test_no_orphan_blobs(self):
        referenced = set()
        for path in glob.glob(os.path.join(CASSETTES, '**', '*.json'), recursive=True):
            if path.endswith('.vars.json'):
                continue
            with open(path) as f:
                for item in json.load(f)['interactions']:
                    for body in (item['request'].get('body'), item['response'].get('body')):
                        if isinstance(body, dict) and 'blob' in body:
                            referenced.add(body['blob'])
        stored = {os.path.basename(p)[:-4] for p in glob.glob(os.path.join(CASSETTES, '_blobs', '*', '*.bin'))}
        assert stored == referenced, f'{len(stored - referenced)} orphan blob(s), {len(referenced - stored)} missing'

    @pytest.mark.skipif(proxy.find_mitmdump() is None, reason='mitmdump (mitmproxy) is not installed')
    def test_flows(self):
        leaks = maintenance.leaks_in_flows(CASSETTES)
        assert not leaks, f'secrets in recorded flows, run python -m test.testings.hfvcr.maintenance: {leaks}'

"""
Maintenance of what is already recorded: ``python -m test.testings.hfvcr.maintenance [--cassettes DIR]``.

``rescrub`` applies the *current* rules of :mod:`.redact` to every cassette (``*.json`` and the blob store) and every recorded
flow (``*.mitm``, needs ``mitmdump``). Run it whenever the rules grow; ``test/hfvcr/test_cassettes_clean.py`` is the guard that
fails when something that must not be committed is still there.
"""
import argparse
import glob
import json
import os
import shutil
import sys
import tempfile
from typing import Dict, List, Tuple

from . import redact, proxy
from .serializer import BlobJsonSerializer


def _rescrub_interaction(item: dict) -> bool:
    """Apply the rules to one deserialized interaction in place, ``True`` when something changed."""
    changed = False
    request, response = item['request'], item['response']
    uri = redact.redact_str(request['uri'])
    changed |= uri != request['uri']
    request['uri'] = uri
    for headers, names in ((request.get('headers') or {}, redact.REQUEST_HEADERS),
                           (response.get('headers') or {}, redact.RESPONSE_HEADERS)):
        for name in list(headers):
            if name.lower() in names:
                del headers[name]
                changed = True
            else:
                values = headers[name] if isinstance(headers[name], list) else [headers[name]]
                new = redact.header_values(name, values)
                if new != values:
                    headers[name] = new
                    changed = True
    body = response['body']['string']
    if isinstance(body, str):
        body = body.encode('utf-8')
        as_text = True
    else:
        as_text = False
    if body:
        new = redact.redact_bytes(body)
        if new != body:
            response['body']['string'] = new.decode('utf-8') if as_text else new
            for name in list(response.get('headers') or {}):
                if name.lower() == 'content-length':
                    response['headers'][name] = [str(len(new))]
            changed = True
    return changed


def rescrub_cassettes(cassette_dir: str) -> Tuple[int, int]:
    """Re-scrub every ``*.json`` cassette, then drop the blobs nothing refers to. Returns (cassettes changed, blobs removed)."""
    serializer = BlobJsonSerializer(os.path.join(cassette_dir, '_blobs'))
    changed_files = 0
    referenced = set()
    paths = [p for p in glob.glob(os.path.join(cassette_dir, '**', '*.json'), recursive=True)
             if not p.endswith('.vars.json') and f'{os.sep}_blobs{os.sep}' not in p]
    for path in sorted(paths):
        with open(path, 'r') as f:
            raw = f.read()
        data = serializer.deserialize(raw)
        changed = False
        for item in data['interactions']:
            changed |= _rescrub_interaction(item)
        new_raw = serializer.serialize(data) if changed else raw
        if changed:
            with open(path, 'w') as f:
                f.write(new_raw)
            changed_files += 1
        for ref in json.loads(new_raw)['interactions']:
            for body in (ref['request'].get('body'), ref['response'].get('body')):
                if isinstance(body, dict) and 'blob' in body:
                    referenced.add(body['blob'])
    removed = 0
    for blob in glob.glob(os.path.join(cassette_dir, '_blobs', '*', '*.bin')):
        if os.path.basename(blob)[:-4] not in referenced:
            os.remove(blob)
            removed += 1
    for directory in glob.glob(os.path.join(cassette_dir, '_blobs', '*')):
        if os.path.isdir(directory) and not os.listdir(directory):
            os.rmdir(directory)
    return changed_files, removed


def rescrub_flows(cassette_dir: str) -> int:
    """Re-scrub every ``*.mitm`` flow file in place. Returns how many were processed."""
    flows = sorted(glob.glob(os.path.join(cassette_dir, '**', '*.mitm'), recursive=True))
    if not flows:
        return 0
    if proxy.find_mitmdump() is None:
        raise SystemExit(f'{len(flows)} recorded flows need mitmdump to be re-scrubbed: set ${proxy.MITMDUMP_ENV} or put it on PATH')
    home = proxy.ProxyHome()
    try:
        for path in flows:
            out = os.path.join(home.path, 'scrubbed.mitm')
            proxy.scrub(home, path, out)
            shutil.move(out, path)
    finally:
        home.cleanup()
    return len(flows)


def leaks_in_flows(cassette_dir: str) -> Dict[str, List[str]]:
    """``{flow file: [LEAK lines]}`` of the flows that still hold something that must not be committed."""
    import subprocess
    check = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'mitm_check.py')
    found = {}
    home = proxy.ProxyHome()
    try:
        for path in sorted(glob.glob(os.path.join(cassette_dir, '**', '*.mitm'), recursive=True)):
            result = subprocess.run([proxy.find_mitmdump(), '-n', '-r', path, '-s', check] + home.common_args(),
                                    stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            lines = sorted({l.strip() for l in result.stdout.decode('utf-8', 'replace').splitlines() if l.startswith('LEAK')})
            if lines:
                found[os.path.relpath(path, cassette_dir)] = lines
    finally:
        home.cleanup()
    return found


def main(argv=None):
    parser = argparse.ArgumentParser(description='Re-scrub recorded cassettes and flows with the current rules.')
    parser.add_argument('--cassettes', default=os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'cassettes'))
    args = parser.parse_args(argv)
    directory = os.path.abspath(args.cassettes)
    files, blobs = rescrub_cassettes(directory)
    print(f'cassettes changed: {files}, orphan blobs removed: {blobs}')
    print(f'flows re-scrubbed: {rescrub_flows(directory)}')


if __name__ == '__main__':
    sys.exit(main())

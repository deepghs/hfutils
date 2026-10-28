"""
Regenerates manifest.json: for every archive of this directory, the members (size and sha256) that an INDEPENDENT tool extracts.

The tests of hfutils.index compare what hfutils reads with this file, so the expected bytes never come from hfutils itself.
Oracles are tried in this order and the first that extracts every member without an error wins (it is written to the manifest):
7-Zip, Info-ZIP `unzip`, and the standard library `zipfile` of Python 3.14 (which also reads zstd).
Needs `7z` and `unzip` on PATH and, optionally, $PYTHON314:    python make_manifest.py
"""
import hashlib
import json
import os
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
PASSWORDS = {'crypto-two-passwords.zip': ['alpha', 'beta']}
DEFAULT_PASSWORD = 'secret'
# the archive is opened from one volume: the others are parts of it
LATER_VOLUMES = ('.z01', '.z02', '.zip.002', '.zip.003')
# PKWARE strong encryption and an encrypted central directory: nothing reads them
NOT_READABLE = {'thirdparty-libarchive-strong-encryption.zip', 'thirdparty-libarchive-encrypted-directory.zip'}


def digest_tree(root):
    members, digests = {}, []
    for base, _, files in os.walk(root):
        for f in files:
            with open(os.path.join(base, f), 'rb') as fh:
                data = fh.read()
            item = {'size': len(data), 'sha256': hashlib.sha256(data).hexdigest()}
            members[os.path.relpath(os.path.join(base, f), root).replace(os.sep, '/')] = item
            digests.append([item['size'], item['sha256']])
    return members, sorted(digests)


def via_7z(archive, password, td):
    return subprocess.run(['7z', 'x', '-y', f'-o{td}', f'-p{password}', archive], capture_output=True).returncode == 0


def via_unzip(archive, password, td):
    return subprocess.run(['unzip', '-qq', '-o', '-P', password, '-d', td, archive], capture_output=True).returncode == 0


def via_py314(archive, password, td):
    py = os.environ.get('PYTHON314')
    if not py:
        return False
    code = ('import sys, zipfile; z = zipfile.ZipFile(sys.argv[1]); z.extractall(sys.argv[2], pwd=sys.argv[3].encode()); '
            'print(len(z.namelist()))')
    return subprocess.run([py, '-c', code, archive, td, password], capture_output=True).returncode == 0


ORACLES = (('7z', via_7z), ('unzip', via_unzip), ('zipfile (Python 3.14)', via_py314))


def extract(archive, password):
    for name, run in ORACLES:
        with tempfile.TemporaryDirectory() as td:
            if run(archive, password, td):
                members, digests = digest_tree(td)
                return {'oracle': name, 'members': members, 'digests': digests}
    return {'oracle': None}


def main():
    manifest = {}
    for name in sorted(os.listdir(HERE)):
        if name.endswith(('.py', '.md', '.sh', '.json')) or name.endswith(LATER_VOLUMES):
            continue
        if name in NOT_READABLE:
            manifest[name] = {'oracle': None, 'reason': 'not readable by any tool: PKWARE strong encryption / encrypted central directory'}
            continue
        entry = extract(os.path.join(HERE, name), DEFAULT_PASSWORD)
        for pw in PASSWORDS.get(name, []):
            entry.setdefault('by_password', {})[pw] = extract(os.path.join(HERE, name), pw)
        manifest[name] = entry
        print(f'{name:48s} oracle={entry["oracle"]} members={len(entry.get("members", {}))}', file=sys.stderr)
    with open(os.path.join(HERE, 'manifest.json'), 'w') as f:
        json.dump(manifest, f, indent=1, sort_keys=True, ensure_ascii=True)
        f.write('\n')


if __name__ == '__main__':
    main()

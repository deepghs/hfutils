"""``hfutils ils`` against a public indexed tar (see ``test/index/public_tar.py``): what it prints is checked against the index."""
import collections
import os
import re

import click
import pytest
from hbutils.testing import simulate_entry

from hfutils.entry import hfutilscli
from hfutils.utils import hf_normpath
from test.index.public_tar import index, REPO, ARCHIVE, IDX_REPO, IDX_FILE, OTHER_IDX_FILE  # noqa: F401

_ARGS = ['hfutils', 'ils', '-r', REPO, '--idx_repository', IDX_REPO, '-a', ARCHIVE]


def _ils(*extra, expect_ok=True):
    result = simulate_entry(hfutilscli, _ARGS + list(extra))
    if expect_ok:
        assert result.exitcode == 0, (f'Exitcode: {result.exitcode!r}\nError: {result.error!r}\n'
                                      f'========= Stdout =========\n{result.stdout}\n'
                                      f'========= Stderr =========\n{result.stderr}\n')
    return click.unstyle(result.stdout).splitlines(keepends=False)


def _rows(index):
    return [{'file': hf_normpath(name), 'raw': name, 'offset': info['offset'], 'size': info['size'], 'sha256': info['sha256']}
            for name, info in index['files'].items()]


@pytest.mark.unittest
class TestEntryIlsPublic:
    def test_default_is_by_offset(self, index):
        want = [r['file'] for r in sorted(_rows(index), key=lambda r: (r['offset'], r['file']))]
        assert _ils() == want

    def test_offset_desc(self, index):
        want = [r['file'] for r in sorted(_rows(index), key=lambda r: (r['offset'], r['file']), reverse=True)]
        assert _ils('-o', 'desc') == want

    def test_name_asc_and_desc(self, index):
        rows = _rows(index)
        assert _ils('-s', 'name') == [r['file'] for r in sorted(rows, key=lambda r: (r['file'], r['offset']))]
        assert _ils('-s', 'name', '-o', 'desc') == \
               [r['file'] for r in sorted(rows, key=lambda r: (r['file'], r['offset']), reverse=True)]

    def test_size_asc_and_desc(self, index):
        rows = _rows(index)
        asc = _ils('-s', 'size')
        assert asc == [r['file'] for r in sorted(rows, key=lambda r: (r['size'], r['offset'], r['file']))]
        assert asc[0] == '2946001.'  # the empty member comes first
        assert _ils('-s', 'size', '-o', 'desc') == \
               [r['file'] for r in sorted(rows, key=lambda r: (r['size'], r['offset'], r['file']), reverse=True)]

    def test_detailed_lists_offset_name_size_and_hash(self, index):
        lines = _ils('-l')
        rows = sorted(_rows(index), key=lambda r: (r['offset'], r['file']))
        assert len(lines) == len(rows)
        parsed = []
        for line in lines:
            offset, _, rest = line.partition(' | ')
            tokens = rest.split()
            parsed.append({'file': tokens[0], 'offset': int(offset), 'sha256': tokens[-1]})
        # the detailed listing shows the names as the archive has them (the plain one normalizes them)
        assert parsed == [{'file': r['raw'], 'offset': r['offset'], 'sha256': r['sha256']} for r in rows]

    def test_detailed_sorted_by_size_desc(self, index):
        lines = _ils('-l', '-s', 'size', '-o', 'desc')
        by_name = {r['raw']: r for r in _rows(index)}
        sizes = [by_name[line.partition(' | ')[2].split()[0]]['size'] for line in lines]
        assert sizes == sorted(sizes, reverse=True)
        assert len(sizes) == len(by_name)

    def test_information(self, index):
        lines = _ils('-I')
        text = '\n'.join(lines)
        assert f'Repo ID: {REPO}' in lines
        assert f'Index Repo ID: {IDX_REPO}' in lines
        assert 'Repo Type: dataset' in lines
        assert 'Revision: main' in lines
        assert f'Archive File: {ARCHIVE}' in lines
        assert f'Native Hash: {index["hash"]}' in lines
        assert f'LFS Hash: {index["hash_lfs"]}' in lines
        assert re.search(rf'^File Size: .*\({index["filesize"]} Bytes\)$', text, re.M), text
        assert re.search(r'Files: .*6775', text)
        counts = collections.Counter(os.path.splitext(name)[1] for name in index['files'])
        for ext, count in counts.most_common(3):
            assert re.search(rf'^\s*{re.escape(ext or "<none>")} : {count} files?$', text, re.M), (ext, count)
        for title in ('Total Size:', 'Average File Size:', 'Median File Size:', 'Smallest File Size:', 'Largest File Size:',
                      'Standard Deviation:', 'Quartiles:', 'Interquartile Range (IQR):'):
            assert title in text
        assert lines[-1] == 'Status: Up-To-Date'

    def test_information_with_an_index_file_and_revision(self):
        lines = _ils('-I', '-i', IDX_FILE, '-R', 'main')
        assert f'Index File: {IDX_FILE}' in lines
        assert lines[-1] == 'Status: Up-To-Date'

    def test_information_of_an_outdated_index(self):
        lines = _ils('-I', '-i', OTHER_IDX_FILE)  # the index of another archive does not describe this one
        assert f'Index File: {OTHER_IDX_FILE}' in lines
        assert 'Status: Outdated' in lines
        assert lines[-1] == 'Index file is recommended to get refreshed.'

    def test_a_missing_archive_fails(self):
        result = simulate_entry(hfutilscli, ['hfutils', 'ils', '-r', REPO, '--idx_repository', IDX_REPO,
                                             '-a', 'original/not-there.tar'])
        assert result.exitcode != 0

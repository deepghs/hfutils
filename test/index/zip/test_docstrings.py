"""The docstrings of ``hfutils/index/zip`` are a published contract (see the style guide in ``AGENTS.md``): every public member says what
its parameters are and what it returns, carries an ``Example::`` and that example is run here, so it cannot drift from the code."""
import ast
import doctest
import glob
import importlib
import os
import re
import shutil

import pytest
from hbutils.testing import isolated_directory

from hfutils.index.zip import fetch as zip_fetch
from test.index.zip.fakehub import FakeHub
from test.testings import get_testfile

PACKAGE_DIR = os.path.join('hfutils', 'index', 'zip')
MODULES = sorted(os.path.splitext(os.path.basename(f))[0] for f in glob.glob(os.path.join(PACKAGE_DIR, '*.py')))

# what the examples find in their directory (and, for the remote functions, in the repository ``owner/repo``)
FILES = {
    'archive.zip': 'methods-bzip2.zip', 'locked.zip': 'crypto-zipcrypto.zip', 'aes.zip': 'crypto-aes256.zip',
    'split.zip.001': 'split-7z.zip.001', 'split.zip.002': 'split-7z.zip.002', 'split.zip.003': 'split-7z.zip.003',
    'gap.zip.001': 'split-7z.zip.001', 'gap.zip.003': 'split-7z.zip.003', 'sjis.zip': 'names-shiftjis.zip',
    'legacy.zip': 'thirdparty-ziprs-shrink.zip', 'ppmd.zip': 'methods-ppmd.zip', 'reduce.zip': 'thirdparty-ziprs-reduce.zip',
    'implode.zip': 'thirdparty-ziprs-implode.zip', 'empty.zip': 'empty.zip',
}


def _have_cryptography():
    try:
        import cryptography  # noqa: F401
        return True
    except ImportError:
        return False


def _prepare():
    for name, fixture in FILES.items():
        shutil.copy(get_testfile('zipfiles', fixture), name)
    with open('notes.txt', 'w') as f:
        f.write('just some text, not an archive\n')


def _public(tree):
    """``(qualified name, node)`` of the public functions, classes and methods of a module (properties apart)."""
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.ClassDef)) and not node.name.startswith('_'):
            yield node.name, node
            if isinstance(node, ast.ClassDef):
                for member in node.body:
                    if isinstance(member, ast.FunctionDef) and (not member.name.startswith('_') or member.name == '__init__'):
                        yield f'{node.name}.{member.name}', member


def _is_property(node):
    return any(isinstance(d, ast.Name) and d.id == 'property' for d in getattr(node, 'decorator_list', []))


@pytest.mark.unittest
class TestZipDocstringStyle:
    @pytest.mark.parametrize('module', MODULES)
    def test_every_public_member_is_documented_in_full(self, module):
        with open(os.path.join(PACKAGE_DIR, f'{module}.py'), encoding='utf-8') as f:
            tree = ast.parse(f.read())
        assert ast.get_docstring(tree), f'{module}: no module docstring'
        problems = []
        classes = {n.name: ast.get_docstring(n) or '' for n in tree.body if isinstance(n, ast.ClassDef)}
        for name, node in _public(tree):
            doc = ast.get_docstring(node) or ''
            if not doc:
                problems.append(f'{name}: no docstring')
                continue
            if isinstance(node, ast.ClassDef):
                if 'Example::' not in doc:
                    problems.append(f'{name}: no Example::')
                continue
            if name.endswith('__init__'):
                owner = classes[name.split('.')[0]]
                where = owner + doc
            else:
                where = doc
            args = [a.arg for a in node.args.posonlyargs + node.args.args + node.args.kwonlyargs if a.arg not in ('self', 'cls')]
            for arg in args:
                if f':param {arg}:' not in where or f':type {arg}:' not in where:
                    problems.append(f'{name}: parameter {arg} lacks :param: / :type:')
            if name.endswith('__init__'):
                continue
            if ':return:' not in doc or ':rtype:' not in doc:
                problems.append(f'{name}: lacks :return: / :rtype:')
            if not _is_property(node) and 'Example::' not in doc:
                problems.append(f'{name}: no Example::')
        assert not problems, '\n'.join(problems)

    @pytest.mark.parametrize('module', MODULES)
    def test_markup_uses_double_backticks(self, module):
        with open(os.path.join(PACKAGE_DIR, f'{module}.py'), encoding='utf-8') as f:
            tree = ast.parse(f.read())
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.ClassDef, ast.Module)):
                doc = ast.get_docstring(node) or ''
                body = '\n'.join(line for line in doc.split('\n') if not line.lstrip().startswith(('>>>', '...')))
                # single backticks may only appear in roles such as :class:`Name`
                leftovers = re.sub(r':[a-z]+:`[^`]+`', '', body.replace('``', ''))
                assert '`' not in leftovers, f'{module}.{getattr(node, "name", "")}: single backticks in {leftovers!r}'


@pytest.mark.unittest
class TestZipDocstringExamples:
    @pytest.mark.parametrize('module', MODULES)
    def test_examples_tell_the_truth(self, module, monkeypatch):
        mod = importlib.import_module(f'hfutils.index.zip.{module}')
        with isolated_directory():
            _prepare()
            hub = FakeHub({name: get_testfile('zipfiles', fixture) for name, fixture in FILES.items()})
            hub.install(monkeypatch)
            globs = {'__name__': mod.__name__}
            finder = doctest.DocTestFinder(exclude_empty=True)
            runner = doctest.DocTestRunner(optionflags=doctest.ELLIPSIS | doctest.NORMALIZE_WHITESPACE)
            tests = [t for t in finder.find(mod, mod.__name__, globs=globs) if t.examples]
            if not _have_cryptography():  # the AES examples decrypt: they need the optional package (the lean CI cells go without)
                tests = [t for t in tests if 'AesDecryptor' not in t.name and 'aes' not in t.name.lower()]
            for t in tests:
                runner.run(t)
            zip_fetch.hf_zip_cache_reset()
            assert runner.failures == 0, f'{module}: {runner.failures} example(s) fail ({runner.tries} run)'

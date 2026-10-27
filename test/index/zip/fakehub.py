"""A fake Hugging Face Hub for the tests that must not touch the network: it answers the two things the remote zip functions ask
for (the size of a file, and a range of its bytes) from local files and keeps count."""
import os
from types import SimpleNamespace

from hfutils.index.zip import fetch as zip_fetch
from hfutils.index.zip.source import HfSource


class FakeHub:
    def __init__(self, files):
        self.files = dict(files)  # path in repo -> local file
        self.paths_info_calls = []
        self.fetches = []  # (path, start, length, token)
        self.tokens = []
        self.fail = None

    def client(self, hf_token=None):
        self.tokens.append(hf_token)
        return self

    def get_paths_info(self, repo_id, paths, repo_type='dataset', revision='main', **_):
        self.paths_info_calls.append(list(paths))
        if self.fail is not None:
            raise self.fail
        return [SimpleNamespace(path=p, size=os.path.getsize(self.files[p]), lfs={'sha256': f'sha-{p}'}, blob_id=None)
                for p in paths if p in self.files]

    def install(self, monkeypatch):
        hub = self

        def fetch(source, start, length):
            hub.fetches.append((source.path, start, length, source.hf_token))
            with open(hub.files[source.path], 'rb') as f:
                f.seek(start)
                return f.read(length)

        monkeypatch.setattr(zip_fetch, 'get_hf_client', hub.client)
        monkeypatch.setattr(HfSource, 'fetch', fetch)
        zip_fetch.hf_zip_cache_reset()
        return hub

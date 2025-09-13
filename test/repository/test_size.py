from typing import List

import pytest
from huggingface_hub.hf_api import RepoFile

from hfutils.repository import RepoFileItem, RepoFileList, hf_hub_repo_analysis


@pytest.fixture
def repo_files() -> List[RepoFile]:
    return [
        RepoFile(path='.gitattributes', size=2798, oid='8db379876c054f22344f9aee0dd0e6dbab45d94e', lfs=None,
                 last_commit=None, security=None),
        RepoFile(path='README.md', size=27746, oid='d87e51a7a47f64e66e5507d882187ecc6e6f5827', lfs=None,
                 last_commit=None, security=None),
        RepoFile(path='exist_ids.json', size=90599754, oid='1c6ed6e6ad050cd088e65debc13132637a527992',
                 lfs=dict(size=90599754, oid='eda6e2aa56bbc6d5b613d9b14c543b9824b0078a294f5645a9d4a4bdf581aa21',
                          pointerSize=133), last_commit=None, security=None),
        RepoFile(path='index_tag_aliases.parquet', size=386176, oid='190e8c8d26a04a284484d20624c69627992fe1ec',
                 lfs=dict(size=386176, oid='40706644b787ea370c33602b7c2591e49aca5124299d1682fbaf1cc9a39de362',
                          pointerSize=131), last_commit=None, security=None),
        RepoFile(path='index_tags.parquet', size=21953695, oid='e0ee5289cb758a6c64b3853645dac4af70b5622c',
                 lfs=dict(size=21953695, oid='d29ebefd42fbb0493fc29408717276f8ba511e18408bf5ffdfa51d1ce4c3cfc9',
                          pointerSize=133), last_commit=None, security=None),
        RepoFile(path='meta.json', size=711, oid='a25d5d0aa6182e2bd47b95b3c5f2b5df136067e0', lfs=None, last_commit=None,
                 security=None),
        RepoFile(path='scanned_archives.json', size=89367, oid='49eceffe6aa9c3260c9f69a45efd276314db0247', lfs=None,
                 last_commit=None, security=None),
        RepoFile(path='tables/gelbooru-1.parquet', size=1129846407, oid='77c8aeb278376426ef8d2665728efa2a14b29097',
                 lfs=dict(size=1129846407, oid='31096ab5bc300122ffeabf04272234852d45ff6ece49e521ee2b97a46a7b4af7',
                          pointerSize=135), last_commit=None, security=None),
        RepoFile(path='tables/gelbooru-2.parquet', size=1412998009, oid='d794f76cd227a9b0d785bb42469b45ff1be5db6d',
                 lfs=dict(size=1412998009, oid='82272718a6d5665476279996bc7bef33b7fc003d070b16192fe2420c692ddd99',
                          pointerSize=135), last_commit=None, security=None),
        RepoFile(path='tables/gelbooru-3.parquet', size=1289893316, oid='47257da159997103777ed19889f83a3aa59e3aa6',
                 lfs=dict(size=1289893316, oid='2d987d309eb996d8439a21bc7a9405ebbb765f32b37641b5853e345fe728fb11',
                          pointerSize=135), last_commit=None, security=None),
        RepoFile(path='tables/gelbooru-4.parquet', size=209674228, oid='517e64705a3bb2f464123c68905a68e4809b07a1',
                 lfs=dict(size=209674228, oid='296982985d45e8581c08cdd2b2d66a14484a274576b0c166d35f9c56d334caf5',
                          pointerSize=134), last_commit=None, security=None),
        RepoFile(path='tags.parquet', size=18186200, oid='469b32999c7ad6798eee62f960b96f4023249d20',
                 lfs=dict(size=18186200, oid='f4f4353ffc07e199ec11eb5baaf1d1dad631200120692241bbb90903a92fbd69',
                          pointerSize=133), last_commit=None, security=None)
    ]


@pytest.mark.unittest
class TestRepoFileItem:
    def test_from_repo_file(self, repo_files):
        item = RepoFileItem.from_repo_file(repo_files[0])
        assert item.path == '.gitattributes'
        assert item.size == 2798
        assert not item.is_lfs
        assert item.lfs_sha256 is None
        assert item.blob_id == '8db379876c054f22344f9aee0dd0e6dbab45d94e'

        item_lfs = RepoFileItem.from_repo_file(repo_files[2])
        assert item_lfs.path == 'exist_ids.json'
        assert item_lfs.size == 90599754
        assert item_lfs.is_lfs
        assert item_lfs.lfs_sha256 == 'eda6e2aa56bbc6d5b613d9b14c543b9824b0078a294f5645a9d4a4bdf581aa21'
        assert item_lfs.blob_id == '1c6ed6e6ad050cd088e65debc13132637a527992'

    def test_path_segments(self, repo_files):
        item = RepoFileItem.from_repo_file(repo_files[7])
        assert item.path_segments == ('tables', 'gelbooru-1.parquet')

    def test_repr(self, repo_files):
        item = RepoFileItem.from_repo_file(repo_files[0])
        assert repr(item) == '<RepoFileItem .gitattributes, size: 2.8 kB>'

        item_lfs = RepoFileItem.from_repo_file(repo_files[2])
        assert repr(item_lfs) == '<RepoFileItem exist_ids.json, size: 90.6 MB (LFS)>'


@pytest.mark.unittest
class TestRepoFileList:
    def test_init(self, repo_files):
        items = [RepoFileItem.from_repo_file(rf) for rf in repo_files]
        repo_file_list = RepoFileList('test-repo', items)
        assert repo_file_list.repo_id == 'test-repo'
        assert repo_file_list.repo_type == 'dataset'
        assert repo_file_list.revision == 'main'
        assert repo_file_list.subdir == '.'
        assert len(repo_file_list) == len(repo_files)
        assert repo_file_list.total_size == sum(rf.size for rf in repo_files)

    def test_getitem(self, repo_files):
        items = [RepoFileItem.from_repo_file(rf) for rf in repo_files]
        repo_file_list = RepoFileList('test-repo', items)
        assert repo_file_list[0].path == '.gitattributes'
        assert repo_file_list[-1].path == 'tags.parquet'

    def test_repr(self, repo_files):
        items = [RepoFileItem.from_repo_file(rf) for rf in repo_files]
        repo_file_list = RepoFileList('test-repo', items)
        repr_str = repo_file_list.repr(max_items=5)
        assert 'test-repo' in repr_str
        assert '12 files' in repr_str
        assert '4.17 GB' in repr_str
        assert '.gitattributes' in repr_str
        assert 'README.md' in repr_str
        assert 'exist_ids.json' in repr_str
        assert 'index_tag_aliases.parquet' in repr_str
        assert 'index_tags.parquet' in repr_str
        assert 'meta.json' not in repr_str
        assert 'scanned_archives.json' not in repr_str
        assert 'tables/gelbooru-1.parquet' not in repr_str
        assert 'tables/gelbooru-2.parquet' not in repr_str
        assert 'tables/gelbooru-3.parquet' not in repr_str
        assert '... (12 files) in total ...' in repr_str

    def test___repr__(self, repo_files):
        items = [RepoFileItem.from_repo_file(rf) for rf in repo_files]
        repo_file_list = RepoFileList('test-repo', items)
        repr_str = repr(repo_file_list)
        assert 'test-repo' in repr_str
        assert '12 files' in repr_str
        assert '4.17 GB' in repr_str
        assert '.gitattributes' in repr_str
        assert 'README.md' in repr_str
        assert 'exist_ids.json' in repr_str
        assert 'index_tag_aliases.parquet' in repr_str
        assert 'index_tags.parquet' in repr_str
        assert 'meta.json' in repr_str
        assert 'scanned_archives.json' in repr_str
        assert 'tables/gelbooru-1.parquet' in repr_str
        assert 'tables/gelbooru-2.parquet' in repr_str
        assert 'tables/gelbooru-3.parquet' in repr_str
        assert '... (12 files) in total ...' in repr_str

    def test_repr_no_limit(self, repo_files):
        items = [RepoFileItem.from_repo_file(rf) for rf in repo_files]
        repo_file_list = RepoFileList('test-repo', items)
        repr_str = repo_file_list.repr(max_items=None)
        assert 'test-repo' in repr_str
        assert '12 files' in repr_str
        assert '4.17 GB' in repr_str
        assert all(rf.path in repr_str for rf in repo_files)
        assert '... (12 files) in total ...' not in repr_str

    def test_hf_hub_repo_analysis(self):
        repo_file_list = hf_hub_repo_analysis(
            repo_id='deepghs/gelbooru_index',
        )
        assert repo_file_list.repo_id == 'deepghs/gelbooru_index'
        assert repo_file_list.repo_type == 'dataset'
        assert repo_file_list.revision == 'main'
        assert repo_file_list.subdir == '.'

        assert [item.path for item in repo_file_list] == \
               ['.gitattributes', 'README.md', 'exist_ids.json', 'index_tag_aliases.parquet', 'index_tags.parquet',
                'meta.json', 'scanned_archives.json', 'tables/gelbooru-1.parquet', 'tables/gelbooru-2.parquet',
                'tables/gelbooru-3.parquet', 'tables/gelbooru-4.parquet', 'tags.parquet']
        assert len(repo_file_list) == 12
        assert repo_file_list.total_size >= 4100000000

    def test_hf_hub_repo_analysis_subdir(self):
        repo_file_list = hf_hub_repo_analysis(
            repo_id='deepghs/gelbooru_index',
            subdir='tables',
        )
        assert repo_file_list.repo_id == 'deepghs/gelbooru_index'
        assert repo_file_list.repo_type == 'dataset'
        assert repo_file_list.revision == 'main'
        assert repo_file_list.subdir == 'tables'

        assert [item.path for item in repo_file_list] == \
               ['gelbooru-1.parquet', 'gelbooru-2.parquet', 'gelbooru-3.parquet', 'gelbooru-4.parquet']
        assert len(repo_file_list) == 4
        assert repo_file_list.total_size >= 4000000000
        assert repo_file_list.total_size == sum([item.size for item in repo_file_list])

import pytest
from huggingface_hub import scan_cache_dir

from hfutils.cache import delete_detached_cache, delete_cache


@pytest.mark.unittest
class TestCacheDelete:
    def test_mock(self, simple_cachedir):
        hf_cache_info = scan_cache_dir(simple_cachedir)
        assert hf_cache_info.size_on_disk == 2791774
        assert len(hf_cache_info.repos) == 1

        repo = list(hf_cache_info.repos)[0]
        assert len(repo.revisions) == 2

    def test_delete_detached_cache(self, simple_cachedir):
        delete_detached_cache(cache_dir=simple_cachedir)
        hf_cache_info = scan_cache_dir(simple_cachedir)
        assert hf_cache_info.size_on_disk == 1395976
        assert len(hf_cache_info.repos) == 1

        repo = list(hf_cache_info.repos)[0]
        assert len(repo.revisions) == 1

    def test_delete_detached_with_name(self, simple_cachedir):
        delete_detached_cache(cache_dir=simple_cachedir, repo_id='deepghs/hfcache_test_target_repo')
        hf_cache_info = scan_cache_dir(simple_cachedir)
        assert hf_cache_info.size_on_disk == 1395976
        assert len(hf_cache_info.repos) == 1

        repo = list(hf_cache_info.repos)[0]
        assert len(repo.revisions) == 1

    def test_delete_detached_with_name_2(self, simple_cachedir):
        delete_detached_cache(cache_dir=simple_cachedir, repo_id='deepghs/hfcache_test_target_repo2')
        hf_cache_info = scan_cache_dir(simple_cachedir)
        assert hf_cache_info.size_on_disk == 2791774
        assert len(hf_cache_info.repos) == 1

        repo = list(hf_cache_info.repos)[0]
        assert len(repo.revisions) == 2

    def test_delete_detached_with_name_and_type(self, simple_cachedir):
        delete_detached_cache(cache_dir=simple_cachedir,
                              repo_id='deepghs/hfcache_test_target_repo', repo_type='dataset')
        hf_cache_info = scan_cache_dir(simple_cachedir)
        assert hf_cache_info.size_on_disk == 1395976
        assert len(hf_cache_info.repos) == 1

        repo = list(hf_cache_info.repos)[0]
        assert len(repo.revisions) == 1

    def test_delete_detached_with_name_and_type_2(self, simple_cachedir):
        delete_detached_cache(cache_dir=simple_cachedir,
                              repo_id='deepghs/hfcache_test_target_repo', repo_type='model')
        hf_cache_info = scan_cache_dir(simple_cachedir)
        assert hf_cache_info.size_on_disk == 2791774
        assert len(hf_cache_info.repos) == 1

        repo = list(hf_cache_info.repos)[0]
        assert len(repo.revisions) == 2

    def test_delete_detached_with_name_and_type_3(self, simple_cachedir):
        delete_detached_cache(cache_dir=simple_cachedir,
                              repo_id='deepghs/hfcache_test_target_repox', repo_type='dataset')
        hf_cache_info = scan_cache_dir(simple_cachedir)
        assert hf_cache_info.size_on_disk == 2791774
        assert len(hf_cache_info.repos) == 1

        repo = list(hf_cache_info.repos)[0]
        assert len(repo.revisions) == 2

    def test_delete_detached_with_type(self, simple_cachedir):
        delete_detached_cache(cache_dir=simple_cachedir, repo_type='dataset')
        hf_cache_info = scan_cache_dir(simple_cachedir)
        assert hf_cache_info.size_on_disk == 1395976
        assert len(hf_cache_info.repos) == 1

        repo = list(hf_cache_info.repos)[0]
        assert len(repo.revisions) == 1

    def test_delete_detached_with_type_2(self, simple_cachedir):
        delete_detached_cache(cache_dir=simple_cachedir, repo_type='model')
        hf_cache_info = scan_cache_dir(simple_cachedir)
        assert hf_cache_info.size_on_disk == 2791774
        assert len(hf_cache_info.repos) == 1

        repo = list(hf_cache_info.repos)[0]
        assert len(repo.revisions) == 2

    def test_delete_cache(self, simple_cachedir):
        delete_cache(cache_dir=simple_cachedir)
        hf_cache_info = scan_cache_dir(simple_cachedir)
        assert hf_cache_info.size_on_disk == 0
        assert len(hf_cache_info.repos) == 0

    def test_delete_with_name(self, simple_cachedir):
        delete_cache(cache_dir=simple_cachedir, repo_id='deepghs/hfcache_test_target_repo')
        hf_cache_info = scan_cache_dir(simple_cachedir)
        assert hf_cache_info.size_on_disk == 0
        assert len(hf_cache_info.repos) == 0

    def test_delete_with_name_2(self, simple_cachedir):
        delete_cache(cache_dir=simple_cachedir, repo_id='deepghs/hfcache_test_target_repo2')
        hf_cache_info = scan_cache_dir(simple_cachedir)
        assert hf_cache_info.size_on_disk == 2791774
        assert len(hf_cache_info.repos) == 1

        repo = list(hf_cache_info.repos)[0]
        assert len(repo.revisions) == 2

    def test_delete_with_name_and_type(self, simple_cachedir):
        delete_cache(cache_dir=simple_cachedir,
                     repo_id='deepghs/hfcache_test_target_repo', repo_type='dataset')
        hf_cache_info = scan_cache_dir(simple_cachedir)
        assert hf_cache_info.size_on_disk == 0
        assert len(hf_cache_info.repos) == 0

    def test_delete_with_name_and_type_2(self, simple_cachedir):
        delete_cache(cache_dir=simple_cachedir,
                     repo_id='deepghs/hfcache_test_target_repo', repo_type='model')
        hf_cache_info = scan_cache_dir(simple_cachedir)
        assert hf_cache_info.size_on_disk == 2791774
        assert len(hf_cache_info.repos) == 1

        repo = list(hf_cache_info.repos)[0]
        assert len(repo.revisions) == 2

    def test_delete_with_name_and_type_3(self, simple_cachedir):
        delete_cache(cache_dir=simple_cachedir,
                     repo_id='deepghs/hfcache_test_target_repox', repo_type='dataset')
        hf_cache_info = scan_cache_dir(simple_cachedir)
        assert hf_cache_info.size_on_disk == 2791774
        assert len(hf_cache_info.repos) == 1

        repo = list(hf_cache_info.repos)[0]
        assert len(repo.revisions) == 2

    def test_delete_with_type(self, simple_cachedir):
        delete_cache(cache_dir=simple_cachedir, repo_type='dataset')
        hf_cache_info = scan_cache_dir(simple_cachedir)
        assert hf_cache_info.size_on_disk == 0
        assert len(hf_cache_info.repos) == 0

    def test_delete_with_type_2(self, simple_cachedir):
        delete_cache(cache_dir=simple_cachedir, repo_type='model')
        hf_cache_info = scan_cache_dir(simple_cachedir)
        assert hf_cache_info.size_on_disk == 2791774
        assert len(hf_cache_info.repos) == 1

        repo = list(hf_cache_info.repos)[0]
        assert len(repo.revisions) == 2

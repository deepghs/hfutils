import pytest

from hfutils.repository import hf_hub_rollback


@pytest.fixture()
def hf_repo_two_commits(hf_repo, hf_client, hf_vcr):
    """The group: repository (segment ``repo``) -> two commits (segment ``commits``) -> the test body."""
    with hf_vcr.segment('commits'):
        first = hf_client.upload_file(
            path_or_fileobj=b'version one\n', path_in_repo='a.txt', repo_id=hf_repo, repo_type='dataset',
        ).oid
        second = hf_client.upload_file(
            path_or_fileobj=b'version two\n', path_in_repo='b.txt', repo_id=hf_repo, repo_type='dataset',
        ).oid
    yield hf_repo, first, second


@pytest.mark.unittest
class TestRepositoryRollback:
    @pytest.mark.hf_git  # git clone, reset and `git push -f` are recorded and replayed through mitmproxy
    def test_hf_hub_rollback(self, hf_repo_two_commits, hf_client):
        repo, first, second = hf_repo_two_commits
        assert first != second

        hf_hub_rollback(repo, rollback_to=first, repo_type='dataset', silent=True)

        assert hf_client.list_repo_commits(repo, repo_type='dataset')[0].commit_id == first
        files = hf_client.list_repo_files(repo, repo_type='dataset')
        assert 'a.txt' in files
        assert 'b.txt' not in files

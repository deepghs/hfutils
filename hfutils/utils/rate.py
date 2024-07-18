import math
from functools import lru_cache

from pyrate_limiter import Rate, Limiter, Duration

from .path import RepoTypeTyping


def _uncached_commit_create_limiter(repo_id: str, repo_type: RepoTypeTyping):
    # rate limit of each repo on hf is 120 commits per hour
    # otherwise you will get HTTP 429
    # so a hard limit of 1 commit per 30 secs should be safe
    _ = repo_id, repo_type
    rate = Rate(1, int(math.ceil(Duration.SECOND * 30)))
    return Limiter(rate, max_delay=1 << 32)


@lru_cache()
def get_commit_create_limiter(repo_id: str, repo_type: RepoTypeTyping = 'dataset'):
    return _uncached_commit_create_limiter(repo_id=repo_id, repo_type=repo_type)

"""
This module provides functionality for rate limiting commit operations on Hugging Face repositories.
It includes a function to create a rate limiter and a cached version of this function for efficient reuse.
The rate limiting is designed to prevent HTTP 429 errors by adhering to Hugging Face's commit rate limits.
"""

import math
from functools import lru_cache

from pyrate_limiter import Rate, Limiter, Duration

from .path import RepoTypeTyping


def _uncached_commit_create_limiter(repo_id: str, repo_type: RepoTypeTyping):
    """
    Create a rate limiter for commit operations on a Hugging Face repository.

    This function creates a Limiter object that restricts commits to 1 per 30 seconds,
    which is well within Hugging Face's limit of 120 commits per hour.

    :param repo_id: The ID of the repository.
    :type repo_id: str
    :param repo_type: The type of the repository (e.g., 'dataset', 'model').
    :type repo_type: RepoTypeTyping

    :return: A Limiter object configured for the specified repository.
    :rtype: Limiter

    :note: The repo_id and repo_type parameters are not used in the current implementation
           but are included for potential future use or compatibility.
    """
    # rate limit of each repo on hf is 120 commits per hour
    # otherwise you will get HTTP 429
    # so a hard limit of 1 commit per 30 secs should be safe
    _ = repo_id, repo_type
    rate = Rate(1, int(math.ceil(Duration.SECOND * 30)))
    return Limiter(rate, max_delay=1 << 32)


@lru_cache()
def get_commit_create_limiter(repo_id: str, repo_type: RepoTypeTyping = 'dataset'):
    """
    Get a cached rate limiter for commit operations on a Hugging Face repository.

    This function is a cached wrapper around _uncached_commit_create_limiter.
    It returns the same Limiter object for repeated calls with the same parameters,
    improving efficiency for frequent limiter requests.

    :param repo_id: The ID of the repository.
    :type repo_id: str
    :param repo_type: The type of the repository. Defaults to 'dataset'.
    :type repo_type: RepoTypeTyping

    :return: A cached Limiter object configured for the specified repository.
    :rtype: Limiter

    :note: The caching is based on both repo_id and repo_type, so different combinations
           will result in different cached Limiter objects.
    """
    return _uncached_commit_create_limiter(repo_id=repo_id, repo_type=repo_type)

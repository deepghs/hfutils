import logging
from functools import partial
from typing import Optional, Callable

from huggingface_hub import scan_cache_dir, CachedRepoInfo, CachedRevisionInfo, DeleteCacheStrategy


def _collect_revisions(fn: Callable[[CachedRepoInfo, CachedRevisionInfo], bool], cache_dir: Optional[str] = None) \
        -> DeleteCacheStrategy:
    """
    Collects revisions from the cache that match a given criterion and prepares them for deletion.

    :param fn: A function that takes a CachedRepoInfo and CachedRevisionInfo and returns a boolean indicating
               whether the revision should be deleted.
    :type fn: Callable[[CachedRepoInfo, CachedRevisionInfo], bool]
    :param cache_dir: The directory where the cache is stored. If None, uses the default directory.
    :type cache_dir: Optional[str]
    :return: A DeleteCacheStrategy object that can be executed to delete the collected revisions.
    :rtype: DeleteCacheStrategy
    """
    revision_hashes = set()
    scan = scan_cache_dir(cache_dir=cache_dir)
    for repo in scan.repos:
        for revision in repo.revisions:
            if fn(repo, revision):
                revision_hashes.add(revision.commit_hash)
    logging.info(f'Revisions to delete from huggingface cache: {sorted(revision_hashes)}')
    return scan.delete_revisions(*revision_hashes)


def _is_repo_match(repo: CachedRepoInfo, repo_id: Optional[str] = None, repo_type: Optional[str] = None) -> bool:
    if repo_id and repo_type:
        return repo.repo_id == repo_id and repo.repo_type == repo_type
    elif repo_id:
        return repo.repo_id == repo_id
    elif repo_type:
        return repo.repo_type == repo_type
    else:
        return True


def _is_detached_revision(
        repo: CachedRepoInfo, revision: CachedRevisionInfo,
        repo_id: Optional[str] = None, repo_type: Optional[str] = None,
) -> bool:
    """
    Determines if a revision is detached (i.e., not referenced by any branch or tag).

    :param repo: The repository information.
    :type repo: CachedRepoInfo
    :param revision: The revision information.
    :type revision: CachedRevisionInfo
    :param repo_id: The ID of the repository to match. If None, matches any repository ID.
    :type repo_id: Optional[str]
    :param repo_type: The type of the repository to match. If None, matches any repository type.
    :type repo_type: Optional[str]
    :return: True if the revision is detached and matches the given criteria, False otherwise.
    :rtype: bool
    """
    if len(revision.refs) == 0:
        return _is_repo_match(repo, repo_id, repo_type)
    else:
        return False


def delete_detached_cache(
        repo_id: Optional[str] = None, repo_type: Optional[str] = None,
        cache_dir: Optional[str] = None
):
    """
    Deletes all detached revisions from the cache that match the given repository ID and type.

    :param repo_id: The ID of the repository to filter by. If None, matches any repository ID.
    :type repo_id: Optional[str]
    :param repo_type: The type of the repository to filter by. If None, matches any repository type.
    :type repo_type: Optional[str]
    :param cache_dir: The directory where the cache is stored. If None, uses the default directory.
    :type cache_dir: Optional[str]
    """
    # noinspection PyTypeChecker
    strategy = _collect_revisions(
        fn=partial(
            _is_detached_revision,
            repo_id=repo_id,
            repo_type=repo_type,
        ),
        cache_dir=cache_dir,
    )
    logging.info(f'{strategy.expected_freed_size_str} space will be freed.')
    strategy.execute()


def _is_selected_revision(
        repo: CachedRepoInfo, revision: CachedRevisionInfo,
        repo_id: Optional[str] = None, repo_type: Optional[str] = None,
) -> bool:
    """
    Determines if a revision matches the specified repository ID and type.

    :param repo: The repository information.
    :type repo: CachedRepoInfo
    :param revision: The revision information.
    :type revision: CachedRevisionInfo
    :param repo_id: The ID of the repository to match. If None, matches any repository ID.
    :type repo_id: Optional[str]
    :param repo_type: The type of the repository to match. If None, matches any repository type.
    :type repo_type: Optional[str]
    :return: True if the revision matches the given criteria, False otherwise.
    :rtype: bool
    """
    _ = repo, revision
    return _is_repo_match(repo, repo_id, repo_type)


def delete_cache(
        repo_id: Optional[str] = None, repo_type: Optional[str] = None,
        cache_dir: Optional[str] = None
):
    """
    Deletes all revisions from the cache that match the given repository ID and type.

    :param repo_id: The ID of the repository to filter by. If None, matches any repository ID.
    :type repo_id: Optional[str]
    :param repo_type: The type of the repository to filter by. If None, matches any repository type.
    :type repo_type: Optional[str]
    :param cache_dir: The directory where the cache is stored. If None, uses the default directory.
    :type cache_dir: Optional[str]
    """
    # noinspection PyTypeChecker
    strategy = _collect_revisions(
        fn=partial(
            _is_selected_revision,
            repo_id=repo_id,
            repo_type=repo_type,
        ),
        cache_dir=cache_dir,
    )
    logging.info(f'{strategy.expected_freed_size_str} space will be freed.')
    strategy.execute()

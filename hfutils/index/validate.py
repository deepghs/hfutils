from typing import Optional

from huggingface_hub.hf_api import RepoFile
from huggingface_hub.utils import EntryNotFoundError, RepositoryNotFoundError

from .fetch import hf_tar_get_index
from ..operate.base import RepoTypeTyping, get_hf_client


def hf_tar_item_validate(file_item: RepoFile, size: int, hash_: Optional[str] = None, hash_lfs: Optional[str] = None):
    """
    Validate a file item in a tar archive.

    This function checks if the file item matches the expected size and hash.

    :param file_item: The file item from the Hugging Face repository.
    :type file_item: RepoFile
    :param size: The expected size of the file.
    :type size: int
    :param hash_: The expected SHA-1 hash of the file.
    :type hash_: str, optional
    :param hash_lfs: The expected SHA-256 hash of the file if stored in LFS.
    :type hash_lfs: str, optional
    :return: True if the file item is valid, False otherwise.
    :rtype: bool
    """
    # size not match
    if (file_item.lfs and size != file_item.lfs.size) or \
            (not file_item.lfs and size != file_item.size):
        return False

    # compare tar file hash
    item_hashes = [file_item.blob_id]
    if file_item.lfs:
        item_hashes.append(file_item.lfs.sha256)
    item_hashes = set(filter(bool, item_hashes))
    cmp_hashes = [hash_, hash_lfs]
    cmp_hashes = set(filter(bool, cmp_hashes))
    return bool(cmp_hashes & item_hashes)


def hf_tar_validate(repo_id: str, archive_in_repo: str, repo_type: RepoTypeTyping = 'dataset', revision: str = 'main',
                    idx_repo_id: Optional[str] = None, idx_file_in_repo: Optional[str] = None,
                    idx_repo_type: Optional[RepoTypeTyping] = None, idx_revision: Optional[str] = None,
                    hf_token: Optional[str] = None):
    """
    Validate a tar archive in a Hugging Face repository.

    This function validates if the tar archive in the Hugging Face repository matches the expected size and hash.

    .. note::
        This function is based on Huggingface API and hash information in index files, no tar file will be downloaded.

    :param repo_id: The ID of the Hugging Face repository.
    :type repo_id: str
    :param archive_in_repo: The path to the tar archive in the repository.
    :type archive_in_repo: str
    :param repo_type: The type of the Hugging Face repository, defaults to 'dataset'.
    :type repo_type: RepoTypeTyping, optional
    :param revision: The revision of the repository, defaults to 'main'.
    :type revision: str, optional
    :param idx_repo_id: The ID of the repository where the index file is stored.
    :type idx_repo_id: Optional[str], optional
    :param idx_file_in_repo: The path to the index file in the repository.
    :type idx_file_in_repo: Optional[str], optional
    :param idx_repo_type: The type of the repository where the index file is stored.
    :type idx_repo_type: Optional[RepoTypeTyping], optional
    :param idx_revision: The revision of the repository where the index file is stored.
    :type idx_revision: Optional[str], optional
    :param hf_token: The Hugging Face token for authentication, defaults to None.
    :type hf_token: Optional[str], optional
    :raises EntryNotFoundError: If the specified entry is not found in the repository.
    :raises IsADirectoryError: If the specified entry is a directory.
    :return: True if the tar archive is valid, False otherwise.
    :rtype: bool

    .. note::

        If this function returns `False`, it means the json index is expired and need to be re-generated.

        So this function and :func:`hfutils.index.make.hf_tar_create_index` can be used together to gracefully
        refresh an indexed tar dataset.
    """
    hf_client = get_hf_client(hf_token)

    items = list(hf_client.get_paths_info(
        repo_id=repo_id,
        repo_type=repo_type,
        paths=[archive_in_repo],
        revision=revision,
    ))
    if len(items) == 0:
        raise EntryNotFoundError(f'Entry {repo_type}s/{repo_id}/{archive_in_repo} not found.')
    elif not isinstance(items[0], RepoFile):
        raise IsADirectoryError(f'Entry {repo_type}s/{repo_id}/{archive_in_repo} is a directory, not a file.')
    else:
        item = items[0]

    try:
        index = hf_tar_get_index(
            repo_id=repo_id,
            archive_in_repo=archive_in_repo,
            repo_type=repo_type,
            revision=revision,

            idx_repo_id=idx_repo_id,
            idx_file_in_repo=idx_file_in_repo,
            idx_repo_type=idx_repo_type,
            idx_revision=idx_revision,

            hf_token=hf_token,
        )
    except (EntryNotFoundError, RepositoryNotFoundError):
        return False

    return hf_tar_item_validate(
        file_item=item,
        size=index['filesize'],
        hash_=index.get('hash'),
        hash_lfs=index.get('hash_lfs'),
    )

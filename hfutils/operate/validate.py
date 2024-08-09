import logging
import os
from hashlib import sha256, sha1
from typing import Optional

from huggingface_hub.hf_api import RepoFile
from huggingface_hub.utils import EntryNotFoundError

from .base import RepoTypeTyping, get_hf_client


def _raw_check_local_file(repo_file: RepoFile, local_file: str, chunk_for_hash: int = 1 << 20,
                          soft_mode: bool = False) -> bool:
    """
    Checks if the local file matches the file on the Hugging Face Hub repository.

    :param repo_file: The information of the file on the Hugging Face Hub repository.
    :type repo_file: RepoFile
    :param local_file: The path to the local file.
    :type local_file: str
    :param chunk_for_hash: The chunk size for calculating the hash. Default is 1 << 20.
    :type chunk_for_hash: int
    :param soft_mode: Just check the size of the expected file when enabled. Default is False.
    :type soft_mode: bool
    :return: True if the local file matches the file on the repository, False otherwise.
    :rtype: bool
    """
    filesize = os.path.getsize(local_file)
    if repo_file.size != filesize:
        logging.debug(f'File {local_file!r} size ({filesize}) does not match '
                      f'the remote file {repo_file.path!r} ({repo_file.size}).')
        return False

    if soft_mode:
        return True

    if repo_file.lfs:
        sha = sha256()
        expected_hash = repo_file.lfs.sha256
    else:
        sha = sha1()
        sha.update(f'blob {filesize}\0'.encode('utf-8'))
        expected_hash = repo_file.blob_id

    with open(local_file, 'rb') as f:
        # Make sure the big files will not cause out-of-memory errors
        while True:
            data = f.read(chunk_for_hash)
            if not data:
                break
            sha.update(data)

    actual_hash = sha.hexdigest()
    is_match = actual_hash == expected_hash
    logging.debug(f'Result hash of {local_file!r} ({actual_hash}) '
                  f'{"matches" if is_match else "does not match"} '
                  f'the hash of the remote file {repo_file.path!r} ({expected_hash}).')
    return is_match


def is_local_file_ready(local_file: str, repo_id: str, file_in_repo: str,
                        repo_type: RepoTypeTyping = 'dataset', revision: str = 'main',
                        soft_mode: bool = False, hf_token: Optional[str] = None) -> bool:
    """
    Checks if the local file is ready by comparing it with the file on the Hugging Face Hub repository.

    :param local_file: The path to the local file.
    :type local_file: str
    :param repo_id: The identifier of the repository.
    :type repo_id: str
    :param file_in_repo: The path to the file in the repository.
    :type file_in_repo: str
    :param repo_type: The type of the repository. Default is 'dataset'.
    :type repo_type: RepoTypeTyping
    :param revision: The revision of the repository. Default is 'main'.
    :type revision: str
    :param soft_mode: Just check the size of the expected file when enabled. Default is False.
    :type soft_mode: bool
    :param hf_token: The Hugging Face API token. Default is None.
    :type hf_token: Optional[str]
    :return: True if the local file matches the file on the repository, False otherwise.
    :rtype: bool
    """
    hf_client = get_hf_client(hf_token)
    infos = hf_client.get_paths_info(
        repo_id=repo_id,
        repo_type=repo_type,
        revision=revision,
        paths=[file_in_repo],
    )
    if len(infos) == 0:
        raise EntryNotFoundError(f'Entry {repo_type}s/{repo_id}/{file_in_repo} not found.')
    elif len(infos) == 1:
        return _raw_check_local_file(infos[0], local_file, soft_mode=soft_mode)
    else:
        assert False, f'Should not reach here, multiple files with the same name found - {infos!r}'  # pragma: no cover

import logging
import os
from hashlib import sha256, sha1
from typing import Optional

from huggingface_hub.hf_api import RepoFile
from huggingface_hub.utils import EntryNotFoundError

from .base import RepoTypeTyping, get_hf_client


def _raw_check_local_file(repo_file: RepoFile, local_file: str, chunk_for_hash: int = 1 << 20):
    filesize = os.path.getsize(local_file)
    if repo_file.size != filesize:
        logging.info(f'File {local_file!r} size ({filesize}) not match '
                     f'the remote file {repo_file.path!r} ({repo_file.size}).')
        return False

    if repo_file.lfs:
        sha = sha256()
        expected_hash = repo_file.lfs.sha256
    else:
        sha = sha1()
        sha.update(f'blob {filesize}\0'.encode('utf-8'))
        expected_hash = repo_file.blob_id

    with open(local_file, 'rb') as f:
        # make sure the big files will not cause OOM
        while True:
            data = f.read(chunk_for_hash)
            if not data:
                break
            sha.update(data)

    actual_hash = sha.hexdigest()
    is_match = actual_hash == expected_hash
    logging.info(f'Result hash of {local_file!r} ({actual_hash}) '
                 f'{"match" if is_match else "not match"} '
                 f'with the hash of remote file {repo_file.path!r} ({expected_hash}).')
    return is_match


def is_local_file_ready(local_file: str, repo_id: str, file_in_repo: str,
                        repo_type: RepoTypeTyping = 'dataset', revision: str = 'main',
                        hf_token: Optional[str] = None) -> bool:
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
        return _raw_check_local_file(infos[0], local_file)
    else:
        assert False, f'Should not reach here, multiple files with the same name found - {infos!r}'  # pragma: no cover

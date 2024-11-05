"""
This module provides functionalities for handling and indexing TAR archive files, especially for use with
the Hugging Face ecosystem. It includes functions to create and retrieve index information of TAR archives,
which is crucial for efficient data retrieval and management in large datasets. The module also integrates
with Hugging Face's repository system, allowing for operations like uploading and downloading TAR files
and their indices.

Key functionalities include:

- Extracting index information from TAR files.
- Creating index files for TAR archives locally or in a directory.
- Integrating with Hugging Face repositories to manage TAR archives and their indices.

The module utilizes cryptographic hash functions for data integrity checks and supports operations on both local
and remote repositories. It is designed to work seamlessly with the Hugging Face platform, enabling users to
handle large datasets efficiently.
"""

import glob
import json
import logging
import os
import tarfile
from hashlib import sha256, sha1
from typing import Optional

from .hash import _f_sha256
from ..archive import archive_pack
from ..operate import download_file_to_file, upload_file_to_file, upload_directory_as_directory
from ..operate.base import RepoTypeTyping
from ..utils import TemporaryDirectory, tqdm


def tar_get_index_info(src_tar_file, chunk_for_hash: int = 1 << 20, with_hash: bool = True, silent: bool = False):
    """
    Get the index information of a tar archive file.

    .. note::
        The return value of this function will be directly used as the index json file.

    :param src_tar_file: The path to the source tar archive file.
    :type src_tar_file: str
    :param chunk_for_hash: The chunk size for hashing, defaults to 1 << 20 (1 MB).
    :type chunk_for_hash: int, optional
    :param with_hash: Whether to include file hashes in the index, defaults to True.
    :type with_hash: bool, optional
    :param silent: Whether to suppress progress bars and logging messages, defaults to False.
    :type silent: bool, optional
    :return: The index information of the tar archive file.
    :rtype: dict
    """
    filesize = os.path.getsize(src_tar_file)
    sha_common = sha1()
    sha_common.update(f'blob {filesize}\0'.encode('utf-8'))
    sha_lfs = sha256()
    logging.info(f'Calculating hash of {src_tar_file!r} ...')
    with open(src_tar_file, 'rb') as f:
        # make sure the big files will not cause OOM
        while True:
            data = f.read(chunk_for_hash)
            if not data:
                break
            sha_common.update(data)
            sha_lfs.update(data)

    logging.info(f'Indexing tar file {src_tar_file!r} ...')
    files = {}
    with tarfile.open(src_tar_file, mode='r|') as tar:
        for tarinfo in tqdm(tar, desc=f'Indexing tar file {src_tar_file!r} ...', silent=silent):
            tarinfo: tarfile.TarInfo
            if tarinfo.isreg():
                info = {
                    'offset': tarinfo.offset_data,
                    'size': tarinfo.size,
                }
                if with_hash:
                    with TemporaryDirectory() as td:
                        tar.extract(tarinfo, td)
                        dst_file = os.path.join(td, tarinfo.name)
                        info['sha256'] = _f_sha256(dst_file)

                files[tarinfo.name] = info

    return {
        'filesize': filesize,
        'hash': sha_common.hexdigest(),
        'hash_lfs': sha_lfs.hexdigest(),
        'files': files,
    }


def tar_create_index(src_tar_file, dst_index_file: Optional[str] = None,
                     chunk_for_hash: int = 1 << 20, with_hash: bool = True, silent: bool = False):
    """
    Create an index file for a tar archive file.

    :param src_tar_file: The path to the source tar archive file.
    :type src_tar_file: str
    :param dst_index_file: The path to save the index file, defaults to None.
    :type dst_index_file: str, optional
    :param chunk_for_hash: The chunk size for hashing, defaults to 1 << 20 (1 MB).
    :type chunk_for_hash: int, optional
    :param with_hash: Whether to include file hashes in the index, defaults to True.
    :type with_hash: bool, optional
    :param silent: Whether to suppress progress bars and logging messages, defaults to False.
    :type silent: bool, optional
    :return: The path to the created index file.
    :rtype: str
    """
    body, _ = os.path.splitext(src_tar_file)
    dst_index_file = dst_index_file or f'{body}.json'
    if os.path.dirname(dst_index_file):
        os.makedirs(os.path.dirname(dst_index_file), exist_ok=True)
    with open(dst_index_file, 'w') as f:
        json.dump(tar_get_index_info(src_tar_file, chunk_for_hash, with_hash, silent), f)
    return dst_index_file


def tar_create_index_for_directory(src_tar_directory: str, dst_index_directory: Optional[str] = None,
                                   chunk_for_hash: int = 1 << 20, with_hash: bool = True, silent: bool = False):
    """
    Create index files for all tar archives in a specified directory.

    This function scans through the given directory to find all tar files, generates an index for each,
    and saves these indices to the specified destination directory. If no destination directory is provided,
    indices are saved in the same directory as the tar files.

    :param src_tar_directory: The path to the directory containing tar files.
    :type src_tar_directory: str
    :param dst_index_directory: The path to the directory where index files will be saved, defaults to the same as src_tar_directory.
    :type dst_index_directory: str, optional
    :param chunk_for_hash: The chunk size for hashing, defaults to 1 << 20 (1 MB).
    :type chunk_for_hash: int, optional
    :param with_hash: Whether to include file hashes in the index, defaults to True.
    :type with_hash: bool, optional
    :param silent: Whether to suppress progress bars and logging messages, defaults to False.
    :type silent: bool, optional
    :return: The path to the directory where index files are saved.
    :rtype: str
    """
    dst_index_directory = dst_index_directory or src_tar_directory
    for tar_file in tqdm(glob.glob(os.path.join(src_tar_directory, '**', '*.tar'), recursive=True), silent=silent):
        p_idx_file = os.path.join(dst_index_directory, os.path.relpath(tar_file, src_tar_directory))
        idx_body, _ = os.path.splitext(p_idx_file)
        idx_file = f'{idx_body}.json'
        tar_create_index(
            src_tar_file=tar_file,
            dst_index_file=idx_file,
            chunk_for_hash=chunk_for_hash,
            with_hash=with_hash,
            silent=silent,
        )
    return dst_index_directory


def hf_tar_create_index(repo_id: str, archive_in_repo: str,
                        repo_type: RepoTypeTyping = 'dataset', revision: str = 'main',
                        idx_repo_id: Optional[str] = None, idx_file_in_repo: Optional[str] = None,
                        idx_repo_type: Optional[RepoTypeTyping] = None, idx_revision: Optional[str] = None,
                        chunk_for_hash: int = 1 << 20, with_hash: bool = True, skip_when_synced: bool = True,
                        hf_token: Optional[str] = None, ):
    """
    Create an index file for a tar archive file in a Hugging Face repository.

    :param repo_id: The identifier of the repository.
    :type repo_id: str
    :param archive_in_repo: The path to the tar archive file.
    :type archive_in_repo: str
    :param repo_type: The type of the Hugging Face repository, defaults to 'dataset'.
    :type repo_type: RepoTypeTyping, optional
    :param revision: The revision of the repository, defaults to 'main'.
    :type revision: str, optional
    :param idx_repo_id: The identifier of the index repository, defaults to None.
    :type idx_repo_id: str, optional
    :param idx_file_in_repo: The path to save the index file in the index repository, defaults to None.
    :type idx_file_in_repo: str, optional
    :param idx_repo_type: The type of the index repository, defaults to None.
    :type idx_repo_type: RepoTypeTyping, optional
    :param idx_revision: The revision of the index repository, defaults to None.
    :type idx_revision: str, optional
    :param chunk_for_hash: The chunk size for hashing, defaults to 1 << 20 (1 MB).
    :type chunk_for_hash: int, optional
    :param with_hash: Whether to include file hashes in the index, defaults to True.
    :type with_hash: bool, optional
    :param skip_when_synced: Skip syncing when index is ready, defaults to True.
    :type skip_when_synced: bool
    :param hf_token: The Hugging Face access token, defaults to None.
    :type hf_token: str, optional
    """
    body, _ = os.path.splitext(archive_in_repo)
    default_index_filename = f'{body}.json'

    from .validate import hf_tar_validate
    if skip_when_synced and hf_tar_validate(
            repo_id=repo_id,
            repo_type=repo_type,
            archive_in_repo=archive_in_repo,
            revision=revision,

            idx_repo_id=idx_repo_id or repo_id,
            idx_repo_type=idx_repo_type or repo_type,
            idx_file_in_repo=idx_file_in_repo or default_index_filename,
            idx_revision=idx_revision or revision,

            hf_token=hf_token,
    ):
        logging.info(f'Entry {repo_type}s/{repo_id}/{archive_in_repo} already indexed, skipped.')
        return

    with TemporaryDirectory() as td:
        local_tar_file = os.path.join(td, os.path.basename(archive_in_repo))
        download_file_to_file(
            repo_id=repo_id,
            repo_type=repo_type,
            file_in_repo=archive_in_repo,
            local_file=local_tar_file,
            revision=revision,
            hf_token=hf_token,
        )
        dst_index_file = tar_create_index(local_tar_file, chunk_for_hash=chunk_for_hash, with_hash=with_hash)

        upload_file_to_file(
            repo_id=idx_repo_id or repo_id,
            repo_type=idx_repo_type or repo_type,
            file_in_repo=idx_file_in_repo or default_index_filename,
            local_file=dst_index_file,
            revision=idx_revision or revision,
            hf_token=hf_token,
            message=f'Create index for {repo_type}s/{repo_id}@{revision}/{archive_in_repo}',
        )


def hf_tar_create_from_directory(
        repo_id: str, archive_in_repo: str, local_directory: str,
        repo_type: RepoTypeTyping = 'dataset', revision: str = 'main',
        chunk_for_hash: int = 1 << 20, with_hash: bool = True,
        silent: bool = False, hf_token: Optional[str] = None):
    """
    Create a tar archive file from a local directory and upload it to a Hugging Face repository.

    :param repo_id: The identifier of the repository.
    :type repo_id: str
    :param archive_in_repo: The path to save the tar archive file in the repository.
    :type archive_in_repo: str
    :param local_directory: The path to the local directory to be archived.
    :type local_directory: str
    :param repo_type: The type of the Hugging Face repository, defaults to 'dataset'.
    :type repo_type: RepoTypeTyping, optional
    :param revision: The revision of the repository, defaults to 'main'.
    :type revision: str, optional
    :param chunk_for_hash: The chunk size for hashing, defaults to 1 << 20 (1 MB).
    :type chunk_for_hash: int, optional
    :param with_hash: Whether to include file hashes in the index, defaults to True.
    :type with_hash: bool, optional
    :param silent: Whether to suppress progress bars and logging messages, defaults to False.
    :type silent: bool, optional
    :param hf_token: The Hugging Face access token, defaults to None.
    :type hf_token: str, optional
    """
    _, ext = os.path.splitext(archive_in_repo)
    with TemporaryDirectory() as td:
        local_tar_file = os.path.join(td, archive_in_repo)
        if os.path.dirname(local_tar_file):
            os.makedirs(os.path.dirname(local_tar_file), exist_ok=True)
        archive_pack(
            type_name='tar',
            directory=local_directory,
            archive_file=local_tar_file,
            silent=silent,
        )
        tar_create_index(local_tar_file, chunk_for_hash=chunk_for_hash, with_hash=with_hash, silent=silent)

        upload_directory_as_directory(
            repo_id=repo_id,
            repo_type=repo_type,
            path_in_repo='.',
            local_directory=td,
            revision=revision,
            hf_token=hf_token,
            message=f'Create indexed tar {repo_type}s/{repo_id}@{revision}/{archive_in_repo}'
        )

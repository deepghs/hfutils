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
        for tarinfo in tqdm(tar, desc='Indexing tar file ...', silent=silent):
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
    body, _ = os.path.splitext(src_tar_file)
    dst_index_file = dst_index_file or f'{body}.json'
    with open(dst_index_file, 'w') as f:
        json.dump(tar_get_index_info(src_tar_file, chunk_for_hash, with_hash, silent), f)
    return dst_index_file


def hf_tar_create_index(repo_id: str, filename: str, repo_type: RepoTypeTyping = 'dataset', revision: str = 'main',
                        idx_repo_id: Optional[str] = None, idx_filename: Optional[str] = None,
                        idx_repo_type: Optional[RepoTypeTyping] = None, idx_revision: Optional[str] = None,
                        chunk_for_hash: int = 1 << 20, with_hash: bool = True, hf_token: Optional[str] = None):
    with TemporaryDirectory() as td:
        local_tar_file = os.path.join(td, os.path.basename(filename))
        download_file_to_file(
            repo_id=repo_id,
            repo_type=repo_type,
            file_in_repo=filename,
            local_file=local_tar_file,
            revision=revision,
            hf_token=hf_token,
        )
        dst_index_file = tar_create_index(local_tar_file, chunk_for_hash=chunk_for_hash, with_hash=with_hash)

        body, _ = os.path.splitext(filename)
        default_index_filename = f'{body}.json'
        upload_file_to_file(
            repo_id=idx_repo_id or repo_id,
            repo_type=idx_repo_type or repo_type,
            file_in_repo=idx_filename or default_index_filename,
            local_file=dst_index_file,
            revision=idx_revision or revision,
            hf_token=hf_token,
            message=f'Create index for {repo_type}s/{repo_id}@{revision}/{filename}',
        )


def hf_tar_create_from_directory(
        repo_id: str, archive_in_repo: str, local_directory: str,
        repo_type: RepoTypeTyping = 'dataset', revision: str = 'main',
        chunk_for_hash: int = 1 << 20, with_hash: bool = True,
        silent: bool = False, hf_token: Optional[str] = None):
    _, ext = os.path.splitext(archive_in_repo)
    with TemporaryDirectory() as td:
        local_tar_file = os.path.join(td, archive_in_repo)
        if os.path.dirname(local_tar_file):
            os.makedirs(os.path.dirname(local_tar_file), exist_ok=True)
        archive_pack('tar', local_directory, local_tar_file, silent=silent)
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

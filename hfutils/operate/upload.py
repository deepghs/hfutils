"""
This module provides functions for uploading files and directories to Hugging Face repositories.

The module uses the Hugging Face Hub API client for repository operations.
"""

import datetime
import logging
import math
import os.path
import re
import time
from typing import Optional, List, Union

from hbutils.string import plural_word
from huggingface_hub import CommitOperationAdd, CommitOperationDelete

from .base import RepoTypeTyping, get_hf_client, list_files_in_repository, _IGNORE_PATTERN_UNSET
from ..archive import get_archive_type, archive_pack, archive_writer, archive_splitext
from ..config.meta import __VERSION__
from ..utils import walk_files, TemporaryDirectory, tqdm, walk_files_with_groups, FilesGroup, hf_normpath


def upload_file_to_file(local_file, repo_id: str, file_in_repo: str,
                        repo_type: RepoTypeTyping = 'dataset', revision: str = 'main',
                        message: Optional[str] = None, hf_token: Optional[str] = None):
    """
    Upload a local file to a specified path in a Hugging Face repository.

    :param local_file: The local file path to be uploaded.
    :type local_file: str
    :param repo_id: The identifier of the repository.
    :type repo_id: str
    :param file_in_repo: The file path within the repository.
    :type file_in_repo: str
    :param repo_type: The type of the repository ('dataset', 'model', 'space').
    :type repo_type: RepoTypeTyping
    :param revision: The revision of the repository (e.g., branch, tag, commit hash).
    :type revision: str
    :param message: The commit message for the upload.
    :type message: Optional[str]
    :param hf_token: Huggingface token for API client, use ``HF_TOKEN`` variable if not assigned.
    :type hf_token: str, optional

    :raises: Any exception raised by the Hugging Face Hub API client.

    This function uses the Hugging Face Hub API client to upload a single file to a specified
    repository. It's useful for adding or updating individual files in a repository.
    """
    hf_client = get_hf_client(hf_token)
    hf_client.upload_file(
        repo_id=repo_id,
        repo_type=repo_type,
        path_or_fileobj=local_file,
        path_in_repo=file_in_repo,
        revision=revision,
        commit_message=message or f'Upload file {hf_normpath(file_in_repo)!r} with hfutils v{__VERSION__}',
    )


def upload_directory_as_archive(local_directory, repo_id: str, archive_in_repo: str, pattern: Optional[str] = None,
                                repo_type: RepoTypeTyping = 'dataset', revision: str = 'main',
                                message: Optional[str] = None, silent: bool = False,
                                group_method: Optional[Union[str, int]] = None,
                                max_size_per_pack: Optional[Union[str, float]] = None,
                                hf_token: Optional[str] = None):
    """
    Upload a local directory as an archive file to a specified path in a Hugging Face repository.

    :param local_directory: The local directory path to be uploaded.
    :type local_directory: str
    :param repo_id: The identifier of the repository.
    :type repo_id: str
    :param archive_in_repo: The archive file path within the repository.
    :type archive_in_repo: str
    :param pattern: A pattern to filter files in the local directory.
    :type pattern: Optional[str]
    :param repo_type: The type of the repository ('dataset', 'model', 'space').
    :type repo_type: RepoTypeTyping
    :param revision: The revision of the repository (e.g., branch, tag, commit hash).
    :type revision: str
    :param message: The commit message for the upload.
    :type message: Optional[str]
    :param silent: If True, suppress progress bar output.
    :type silent: bool
    :param group_method: Method for grouping files (None for default, int for segment count).
                         Only applied when ``max_total_size`` is assigned.
    :type group_method: Optional[Union[str, int]]
    :param max_size_per_pack: Maximum total size for each group (can be string like "1GB").
                              When assigned, this function will try to upload with multiple archive files.
    :type max_size_per_pack: Optional[Union[str, float]]
    :param hf_token: Huggingface token for API client, use ``HF_TOKEN`` variable if not assigned.
    :type hf_token: str, optional

    :raises: Any exception raised during archive creation or file upload.

    This function compresses the specified local directory into an archive file and then
    uploads it to the Hugging Face repository. It's useful for uploading entire directories
    as a single file, which can be more efficient for large directories.
    """
    archive_type = get_archive_type(archive_in_repo)
    with TemporaryDirectory() as td:
        if max_size_per_pack is not None:
            file_groups = walk_files_with_groups(
                directory=local_directory,
                pattern=pattern,
                group_method=group_method,
                max_total_size=max_size_per_pack,
                silent=silent,
            )
            if len(file_groups) < 2:
                file_groups = None
        else:
            file_groups = None

        if file_groups is None:
            local_archive_file = os.path.join(td, os.path.basename(archive_in_repo))
            archive_pack(
                type_name=archive_type,
                directory=local_directory,
                archive_file=local_archive_file,
                pattern=pattern,
                silent=silent,
            )
            upload_file_to_file(
                repo_id=repo_id,
                repo_type=repo_type,
                local_file=local_archive_file,
                file_in_repo=archive_in_repo,
                revision=revision,
                message=message or f'Upload archive {hf_normpath(archive_in_repo)!r} with hfutils v{__VERSION__}',
                hf_token=hf_token
            )

        else:
            id_pattern = f'{{x:0{max(len(str(len(file_groups))), 5)}d}}'
            raw_dst_archive_file = os.path.normpath(os.path.join(td, archive_in_repo))
            for gid, group in enumerate(tqdm(file_groups, silent=silent,
                                             desc=f'Making {plural_word(len(file_groups), "package")}'), start=1):
                group: FilesGroup
                dst_archive_file_body, dst_archive_file_ext = archive_splitext(raw_dst_archive_file)
                dst_archive_file = (f'{dst_archive_file_body}'
                                    f'-{id_pattern.format(x=gid)}-of-{id_pattern.format(x=len(file_groups))}'
                                    f'{dst_archive_file_ext}')
                os.makedirs(os.path.dirname(dst_archive_file), exist_ok=True)
                with archive_writer(type_name=archive_type, archive_file=dst_archive_file) as af, \
                        tqdm(group.files, silent=silent,
                             desc=f'Packing {local_directory!r} #{gid}/{len(file_groups)} ...') as progress:
                    for file in progress:
                        af.add(os.path.join(local_directory, file), file)

            upload_directory_as_directory(
                repo_id=repo_id,
                repo_type=repo_type,
                local_directory=td,
                path_in_repo='.',
                revision=revision,
                message=message or f'Upload archive {hf_normpath(archive_in_repo)!r} '
                                   f'({plural_word(len(file_groups), "packs")}) '
                                   f'with hfutils v{__VERSION__}',
                hf_token=hf_token,
            )


_PATH_SEP = re.compile(r'[/\\]+')


def upload_directory_as_directory(
        local_directory, repo_id: str, path_in_repo: str, pattern: Optional[str] = None,
        repo_type: RepoTypeTyping = 'dataset', revision: str = 'main',
        message: Optional[str] = None, time_suffix: bool = True,
        clear: bool = False, ignore_patterns: List[str] = _IGNORE_PATTERN_UNSET,
        hf_token: Optional[str] = None, operation_chunk_size: Optional[int] = None,
        upload_timespan: float = 5.0,
):
    """
    Upload a local directory and its files to a specified path in a Hugging Face repository.

    :param local_directory: The local directory path to be uploaded.
    :type local_directory: str
    :param repo_id: The identifier of the repository.
    :type repo_id: str
    :param path_in_repo: The directory path within the repository.
    :type path_in_repo: str
    :param pattern: A pattern to filter files in the local directory.
    :type pattern: Optional[str]
    :param repo_type: The type of the repository ('dataset', 'model', 'space').
    :type repo_type: RepoTypeTyping
    :param revision: The revision of the repository (e.g., branch, tag, commit hash).
    :type revision: str
    :param message: The commit message for the upload.
    :type message: Optional[str]
    :param time_suffix: If True, append a timestamp to the commit message.
    :type time_suffix: bool
    :param clear: If True, remove files in the repository not present in the local directory.
    :type clear: bool
    :param ignore_patterns: List of file patterns to ignore.
    :type ignore_patterns: List[str]
    :param hf_token: Huggingface token for API client, use ``HF_TOKEN`` variable if not assigned.
    :type hf_token: str, optional
    :param operation_chunk_size: Chunk size of the operations. All the operations will be
        separated into multiple commits when this is set.
    :type operation_chunk_size: Optional[int]
    :param upload_timespan: Upload minimal time interval when chunked uploading enabled.
    :type upload_timespan: float

    :raises: Any exception raised during the upload process.

    This function uploads a local directory to a Hugging Face repository, maintaining its
    structure. It can handle large directories by chunking the upload process and provides
    options for clearing existing files and ignoring specific patterns.

    .. note::
        When `operation_chunk_size` is set, multiple commits will be created. When some commits fail,
        it will roll back to the startup commit, using :func:`hfutils.repository.hf_hub_rollback` function.

    .. warning::
        When `operation_chunk_size` is set, multiple commits will be created. But HuggingFace's repository
        API cannot guarantee the atomic feature of your data. So **this function is not thread-safe**.

    .. note::
        The rate limit of HuggingFace repository commit creation is approximately 120 commits / hour.
        So if you really have a large number of chunks to create, please set the `upload_timespan` to a value
        no less than `30.0` to make sure your uploading will not be rate-limited.
    """
    hf_client = get_hf_client(hf_token)
    if clear:
        pre_exist_files = {
            tuple(file.split('/')) for file in
            list_files_in_repository(
                repo_id=repo_id,
                repo_type=repo_type,
                subdir=path_in_repo,
                revision=revision,
                ignore_patterns=ignore_patterns,
                hf_token=hf_token
            )
        }
    else:
        pre_exist_files = set()

    operations = []
    for file in walk_files(local_directory, pattern=pattern):
        segments = tuple(seg for seg in _PATH_SEP.split(file) if seg)
        if segments in pre_exist_files:
            pre_exist_files.remove(segments)
        operations.append(CommitOperationAdd(
            path_or_fileobj=os.path.join(local_directory, file),
            path_in_repo=f'{path_in_repo}/{"/".join(segments)}',
        ))

    for segments in sorted(pre_exist_files):
        operations.append(CommitOperationDelete(
            path_in_repo=f'{path_in_repo}/{"/".join(segments)}',
        ))

    current_time = datetime.datetime.now().astimezone().strftime('%Y-%m-%d %H:%M:%S %Z')
    commit_message = message or f'Upload directory {hf_normpath(path_in_repo)!r} with hfutils v{__VERSION__}'
    if time_suffix:
        commit_message = f'{commit_message}, on {current_time}'

    if operation_chunk_size:
        initial_commit_id = hf_client.list_repo_commits(
            repo_id=repo_id,
            repo_type=repo_type,
            revision=revision
        )[0].commit_id

        last_upload_at = None
        try:
            total_chunks = int(math.ceil(len(operations) / operation_chunk_size))
            for chunk_id in tqdm(range(total_chunks), desc='Chunked Commits'):
                operation_chunk = operations[chunk_id * operation_chunk_size:(chunk_id + 1) * operation_chunk_size]

                # sleep for the given time
                if last_upload_at:
                    sleep_time = last_upload_at + upload_timespan - time.time()
                    if sleep_time > 0:
                        logging.info(f'Sleep for {sleep_time:.1f}s due to the timespan limitation ...')
                        time.sleep(sleep_time)

                last_upload_at = time.time()
                logging.info(f'Uploading chunk #{chunk_id + 1}, '
                             f'with {plural_word(len(operation_chunk), "operation")} ...')
                hf_client.create_commit(
                    repo_id=repo_id,
                    repo_type=repo_type,
                    revision=revision,
                    operations=operation_chunk,
                    commit_message=f'[Chunk #{chunk_id + 1}/{total_chunks}] {commit_message}',
                )

        except Exception:
            from ..repository import hf_hub_rollback

            logging.error(f'Error found when executing chunked uploading, '
                          f'revision {revision!r} will rollback to {initial_commit_id!r} ...')
            hf_hub_rollback(
                repo_id=repo_id,
                repo_type=repo_type,
                revision=revision,
                rollback_to=initial_commit_id,
                hf_token=hf_token,
            )

            raise

    else:
        hf_client.create_commit(
            repo_id=repo_id,
            repo_type=repo_type,
            revision=revision,
            operations=operations,
            commit_message=commit_message,
        )

import datetime
import os.path
import re
from typing import Optional, List

from huggingface_hub import CommitOperationAdd, CommitOperationDelete

from .base import RepoTypeTyping, get_hf_client, list_files_in_repository, _IGNORE_PATTERN_UNSET
from ..archive import get_archive_type, archive_pack
from ..utils import walk_files, TemporaryDirectory


def upload_file_to_file(local_file, repo_id: str, file_in_repo: str,
                        repo_type: RepoTypeTyping = 'dataset', revision: str = 'main',
                        message: Optional[str] = None):
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
    """
    hf_client = get_hf_client()
    hf_client.upload_file(
        repo_id=repo_id,
        repo_type=repo_type,
        path_or_fileobj=local_file,
        path_in_repo=file_in_repo,
        revision=revision,
        commit_message=message,
    )


def upload_directory_as_archive(local_directory, repo_id: str, archive_in_repo: str,
                                repo_type: RepoTypeTyping = 'dataset', revision: str = 'main',
                                message: Optional[str] = None, silent: bool = False):
    """
    Upload a local directory as an archive file to a specified path in a Hugging Face repository.

    :param local_directory: The local directory path to be uploaded.
    :type local_directory: str
    :param repo_id: The identifier of the repository.
    :type repo_id: str
    :param archive_in_repo: The archive file path within the repository.
    :type archive_in_repo: str
    :param repo_type: The type of the repository ('dataset', 'model', 'space').
    :type repo_type: RepoTypeTyping
    :param revision: The revision of the repository (e.g., branch, tag, commit hash).
    :type revision: str
    :param message: The commit message for the upload.
    :type message: Optional[str]
    :param silent: If True, suppress progress bar output.
    :type silent: bool
    """
    archive_type = get_archive_type(archive_in_repo)
    with TemporaryDirectory() as td:
        local_archive_file = os.path.join(td, os.path.basename(archive_in_repo))
        archive_pack(archive_type, local_directory, local_archive_file, silent=silent)
        upload_file_to_file(local_archive_file, repo_id, archive_in_repo, repo_type, revision, message)


_PATH_SEP = re.compile(r'[/\\]+')


def upload_directory_as_directory(local_directory, repo_id: str, path_in_repo: str,
                                  repo_type: RepoTypeTyping = 'dataset', revision: str = 'main',
                                  message: Optional[str] = None, time_suffix: bool = True,
                                  clear: bool = False, ignore_patterns: List[str] = _IGNORE_PATTERN_UNSET):
    """
    Upload a local directory and its files to a specified path in a Hugging Face repository.

    :param local_directory: The local directory path to be uploaded.
    :type local_directory: str
    :param repo_id: The identifier of the repository.
    :type repo_id: str
    :param path_in_repo: The directory path within the repository.
    :type path_in_repo: str
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
    """
    hf_client = get_hf_client()
    if clear:
        pre_exist_files = {
            tuple(file.split('/')) for file in
            list_files_in_repository(repo_id, repo_type, path_in_repo, revision, ignore_patterns)
        }
    else:
        pre_exist_files = set()

    operations = []
    for file in walk_files(local_directory):
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
    commit_message = message or f'Upload directory {os.path.basename(os.path.abspath(local_directory))!r}'
    if time_suffix:
        commit_message = f'{commit_message}, on {current_time}'

    hf_client.create_commit(
        repo_id=repo_id,
        repo_type=repo_type,
        revision=revision,
        operations=operations,
        commit_message=commit_message,
    )

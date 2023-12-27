import os.path
import shutil
from concurrent.futures import ThreadPoolExecutor
from typing import List

from .base import RepoTypeTyping, list_files_in_repository, _IGNORE_PATTERN_UNSET, get_hf_client
from ..archive import archive_unpack
from ..utils import tqdm, TemporaryDirectory


def download_file_to_file(local_file: str, repo_id: str, file_in_repo: str,
                          repo_type: RepoTypeTyping = 'dataset', revision: str = 'main', silent: bool = False):
    """
    Download a file from a Hugging Face repository and save it to a local file.

    :param local_file: The local file path to save the downloaded file.
    :type local_file: str
    :param repo_id: The identifier of the repository.
    :type repo_id: str
    :param file_in_repo: The file path within the repository.
    :type file_in_repo: str
    :param repo_type: The type of the repository ('dataset', 'model', 'space').
    :type repo_type: RepoTypeTyping
    :param revision: The revision of the repository (e.g., branch, tag, commit hash).
    :type revision: str
    :param silent: If True, suppress progress bar output.
    :type silent: bool
    """
    hf_client = get_hf_client()
    relative_filename = os.path.join(*file_in_repo.split("/"))
    with TemporaryDirectory() as td:
        temp_path = os.path.join(td, relative_filename)
        if os.path.exists(local_file):
            shutil.move(local_file, temp_path)
        if os.path.dirname(local_file):
            os.makedirs(os.path.dirname(local_file), exist_ok=True)

        try:
            hf_client.hf_hub_download(
                repo_id=repo_id,
                repo_type=repo_type,
                filename=file_in_repo,
                revision=revision,
                local_dir=td,
                local_dir_use_symlinks=False,
            )
        finally:
            shutil.move(temp_path, local_file)


def download_archive_as_directory(local_directory: str, repo_id: str, file_in_repo: str,
                                  repo_type: RepoTypeTyping = 'dataset', revision: str = 'main', silent: bool = False):
    """
    Download an archive file from a Hugging Face repository and extract it to a local directory.

    :param local_directory: The local directory path to extract the downloaded archive.
    :type local_directory: str
    :param repo_id: The identifier of the repository.
    :type repo_id: str
    :param file_in_repo: The file path within the repository.
    :type file_in_repo: str
    :param repo_type: The type of the repository ('dataset', 'model', 'space').
    :type repo_type: RepoTypeTyping
    :param revision: The revision of the repository (e.g., branch, tag, commit hash).
    :type revision: str
    :param silent: If True, suppress progress bar output.
    :type silent: bool
    """
    with TemporaryDirectory() as td:
        archive_file = os.path.join(td, os.path.basename(file_in_repo))
        download_file_to_file(archive_file, repo_id, file_in_repo, repo_type, revision, silent=silent)
        archive_unpack(archive_file, local_directory, silent=silent)


def download_directory_as_directory(local_directory: str, repo_id: str, dir_in_repo: str = '.',
                                    repo_type: RepoTypeTyping = 'dataset', revision: str = 'main',
                                    silent: bool = False, ignore_patterns: List[str] = _IGNORE_PATTERN_UNSET):
    """
    Download all files in a directory from a Hugging Face repository to a local directory.

    :param local_directory: The local directory path to save the downloaded files.
    :type local_directory: str
    :param repo_id: The identifier of the repository.
    :type repo_id: str
    :param dir_in_repo: The directory path within the repository.
    :type dir_in_repo: str
    :param repo_type: The type of the repository ('dataset', 'model', 'space').
    :type repo_type: RepoTypeTyping
    :param revision: The revision of the repository (e.g., branch, tag, commit hash).
    :type revision: str
    :param silent: If True, suppress progress bar output.
    :type silent: bool
    :param ignore_patterns: List of file patterns to ignore.
    :type ignore_patterns: List[str]
    """
    files = list_files_in_repository(repo_id, repo_type, dir_in_repo, revision, ignore_patterns)
    progress = tqdm(files, silent=silent, desc=f'Downloading {dir_in_repo!r} ...')

    def _download_one_file(rel_file):
        download_file_to_file(
            local_file=os.path.join(local_directory, rel_file),
            repo_id=repo_id,
            file_in_repo=f'{dir_in_repo}/{rel_file}',
            repo_type=repo_type,
            revision=revision,
            silent=silent
        )
        progress.update()

    tp = ThreadPoolExecutor()
    for file in files:
        tp.submit(_download_one_file, file)
    tp.shutdown(wait=True)

"""
This module provides functionality for creating and managing index repositories for tar archives stored in Hugging Face repositories.

The main features of this module include:
- Adding an 'index' subcommand to a Click CLI application
- Creating index files for tar archives
- Uploading index files to a specified Hugging Face repository
- Managing the upload process with a minimum interval between uploads

The module uses the Hugging Face file system and client for interacting with repositories.
"""

import logging
import os.path
import shutil
import time
from typing import Optional

import click
from hbutils.string import plural_word
from huggingface_hub import configure_http_backend

from .base import CONTEXT_SETTINGS
from ..cache import delete_detached_cache
from ..index import hf_tar_validate, tar_create_index
from ..operate import get_hf_fs, download_file_to_file, upload_directory_as_directory
from ..operate.base import REPO_TYPES, RepoTypeTyping, get_hf_client
from ..utils import tqdm, hf_fs_path, parse_hf_fs_path, TemporaryDirectory, hf_normpath, ColoredFormatter, \
    get_requests_session


def _add_index_subcommand(cli: click.Group) -> click.Group:
    """
    Add the 'index' subcommand to the CLI.

    This function defines and adds the 'index' subcommand to the provided Click CLI application.
    The subcommand is responsible for creating index files for tar archives in a Hugging Face repository
    and uploading them to a specified index repository.

    :param cli: The Click CLI application to which the 'index' subcommand will be added.
    :type cli: click.Group

    :return: The modified Click CLI application with the 'index' subcommand added.
    :rtype: click.Group

    Usage:
        This function is typically called when setting up the CLI application, like this:
        cli = click.Group()
        cli = _add_index_subcommand(cli)
    """

    @cli.command('index', help='Make index repository for tar repository.\n\n'
                               'Set environment $HF_TOKEN to use your own access token.',
                 context_settings=CONTEXT_SETTINGS)
    @click.option('-r', '--repository', 'repo_id', type=str, required=True,
                  help='Repository with tar archives inside.')
    @click.option('-x', '--index_repository', 'idx_repo_id', type=str, default=None,
                  help='Repository to create index files. Use the same repository as `-r` option when not given.',
                  show_default=True)
    @click.option('-t', '--type', 'repo_type', type=click.Choice(REPO_TYPES), default='dataset',
                  help='Type of the HuggingFace repository.', show_default=True)
    @click.option('-R', '--revision', 'revision', type=str, default='main',
                  help='Revision of repository.', show_default=True)
    @click.option('--min_upload_interval', 'min_upload_interval', type=float, default=60,
                  help='Min seconds for uploading to huggingface repository.', show_default=True)
    def index(repo_id: str, idx_repo_id: Optional[str], repo_type: RepoTypeTyping, revision: str,
              min_upload_interval: float):
        """
        Create index files for tar archives in a Hugging Face repository and upload them to a specified index repository.

        This function sets up logging, creates the index repository if it doesn't exist, processes tar archives
        to create index files, and manages the upload process of these index files to the specified repository.

        :param repo_id: The ID of the repository containing tar archives.
        :type repo_id: str
        :param idx_repo_id: The ID of the repository where index files will be uploaded. If None, uses repo_id.
        :type idx_repo_id: Optional[str]
        :param repo_type: The type of the Hugging Face repository (e.g., 'dataset', 'model').
        :type repo_type: RepoTypeTyping
        :param revision: The revision of the repository to use.
        :type revision: str
        :param min_upload_interval: The minimum time interval (in seconds) between uploads to the Hugging Face repository.
        :type min_upload_interval: float

        :raises: Various exceptions may be raised during file system operations or API calls.

        Usage:
            This function is typically invoked through the CLI interface, like:
            $ python script.py index -r my_repo -x my_index_repo -t dataset -R main --min_upload_interval 120
        """
        configure_http_backend(get_requests_session)

        logger = logging.getLogger()
        logger.setLevel(logging.INFO)
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(ColoredFormatter())
        logger.addHandler(console_handler)

        idx_repo_id = idx_repo_id or repo_id
        delete_detached_cache(repo_id=repo_id, repo_type=repo_type)

        hf_client = get_hf_client()
        if not hf_client.repo_exists(repo_id=idx_repo_id, repo_type=repo_type):
            logging.info(f'Creating repository {idx_repo_id!r}, type: {repo_type!r} ...')
            hf_client.create_repo(repo_id=idx_repo_id, repo_type=repo_type)

        hf_fs = get_hf_fs()
        hf_tars = hf_fs.glob(hf_fs_path(repo_id=repo_id, repo_type=repo_type, filename='**/*.tar', revision=revision))
        logging.info(f'{plural_word(len(hf_tars), "tar archive")} found in {repo_type}s/{repo_id} ...')
        with TemporaryDirectory() as upload_dir:
            idx_files = []
            last_uploaded_at: Optional[float] = None

            def _upload(force=False):
                """
                Upload index files to the Hugging Face repository.

                This internal function manages the upload process of index files, respecting the minimum upload interval.

                :param force: If True, upload regardless of the time since the last upload.
                :type force: bool
                """
                nonlocal last_uploaded_at

                if not idx_files:
                    return
                if not force and last_uploaded_at and last_uploaded_at + min_upload_interval > time.time():
                    return

                logging.info(f'Uploading index for {plural_word(len(idx_files), "tar archives")} ...')
                upload_directory_as_directory(
                    repo_id=idx_repo_id,
                    repo_type=repo_type,
                    revision=revision,
                    local_directory=upload_dir,
                    path_in_repo='.',
                    message=f'Index for {plural_word(len(idx_files), "tar archives")} - '
                            f'{", ".join(map(repr, idx_files))}',
                )
                last_uploaded_at = time.time()

                _clean_dir()

            def _clean_dir():
                """
                Clean the temporary upload directory.

                This internal function removes all files and directories in the upload directory.
                """
                logging.info(f'Cleaning upload temporary directory {upload_dir!r} ...')
                for item in os.listdir(upload_dir):
                    dst_file = os.path.join(upload_dir, item)
                    if os.path.isfile(dst_file):
                        os.remove(dst_file)
                    elif os.path.islink(dst_file):
                        os.unlink(dst_file)
                    elif os.path.isdir(dst_file):
                        shutil.rmtree(dst_file)
                idx_files.clear()
                logging.info('Upload directory cleaned.')

            for tar_path in tqdm(hf_tars, desc='Making Indices'):
                tar_filename = parse_hf_fs_path(tar_path).filename
                idx_filename = hf_normpath(os.path.splitext(tar_filename)[0] + '.json')
                if not hf_tar_validate(
                        repo_id=repo_id,
                        repo_type=repo_type,
                        archive_in_repo=tar_filename,
                        idx_repo_id=idx_repo_id,
                        revision=revision,
                ):
                    src_hf_path = hf_fs_path(repo_id=repo_id, repo_type=repo_type,
                                             filename=tar_filename, revision=revision)
                    dst_hf_path = hf_fs_path(repo_id=idx_repo_id, repo_type=repo_type,
                                             filename=idx_filename, revision=revision)
                    logging.info(f'Indexing {src_hf_path!r} --> {dst_hf_path!r} ...')
                    with TemporaryDirectory() as td:
                        local_tar_file = os.path.join(td, os.path.basename(tar_filename))
                        local_idx_file = os.path.join(upload_dir, idx_filename)
                        if os.path.dirname(local_idx_file):
                            os.makedirs(os.path.dirname(local_idx_file), exist_ok=True)

                        download_file_to_file(
                            repo_id=repo_id,
                            repo_type=repo_type,
                            file_in_repo=tar_filename,
                            local_file=local_tar_file,
                            revision=revision,
                        )
                        logging.debug(f'Creating index file {local_tar_file!r} --> {local_idx_file!r} ...')
                        tar_create_index(
                            src_tar_file=local_tar_file,
                            dst_index_file=local_idx_file,
                        )
                        idx_files.append(idx_filename)

                _upload(force=False)

            _upload(force=True)

    return cli

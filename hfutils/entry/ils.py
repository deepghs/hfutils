"""
This module provides functionality for listing files from a HuggingFace repository's index tar file.

It includes a command-line interface (CLI) for interacting with HuggingFace repositories,
specifically for listing and displaying information about files within a repository's
index tar file. The module offers various options for sorting, filtering, and displaying
detailed information about the files and the repository itself.

Key features:

1. List files from a HuggingFace repository's index tar file
2. Display detailed file information
3. Show repository and index file statistics
4. Sort files by different criteria (offset, name, size)
5. Validate the index file's status (up-to-date or outdated)

This module is part of a larger system for interacting with HuggingFace repositories
and provides a user-friendly interface for exploring the contents of index tar files.
"""

import os.path
import statistics
import warnings
from typing import Optional, Literal

import click
from hbutils.scale import size_to_bytes_str
from hbutils.string import plural_word, titleize
from huggingface_hub import configure_http_backend

from .base import CONTEXT_SETTINGS
from ..index import hf_tar_get_index, hf_tar_validate
from ..operate.base import REPO_TYPES
from ..utils import get_requests_session, get_file_type, FileItemType
from ..utils.path import RepoTypeTyping, hf_normpath

_FT_NAME_MAP = {
    FileItemType.IMAGE: 'image',
    FileItemType.ARCHIVE: 'archive/compressed',
    FileItemType.MODEL: 'model',
    FileItemType.DATA: 'data',
    FileItemType.FILE: 'other',
}


def _add_ils_subcommand(cli: click.Group) -> click.Group:
    """
    Add the 'ils' subcommand to the given click Group.

    This function defines and adds the 'ils' (Index List) subcommand to the provided
    click Group. The 'ils' command allows users to list files from a HuggingFace
    repository's index tar file and display various information about the repository
    and its contents.

    :param cli: The click Group to which the 'ils' subcommand will be added.
    :type cli: click.Group

    :return: The modified click Group with the 'ils' subcommand added.
    :rtype: click.Group

    Usage:
        This function is typically called when setting up the CLI for the application.
        It adds the 'ils' command with various options for customizing the output.

    Example:
        cli = click.Group()
        cli = _add_ils_subcommand(cli)
    """

    @cli.command('ils', help='List files from HuggingFace repository\'s index tar file.\n\n'
                             'Set environment $HF_TOKEN to use your own access token.',
                 context_settings=CONTEXT_SETTINGS)
    @click.option('-r', '--repository', 'repo_id', type=str, required=True,
                  help='Repository to download from.')
    @click.option('--idx_repository', 'idx_repo_id', type=str, default=None,
                  help='Index repository to download from.', show_default=True)
    @click.option('-t', '--type', 'repo_type', type=click.Choice(REPO_TYPES), default='dataset',
                  help='Type of the HuggingFace repository.', show_default=True)
    @click.option('-R', '--revision', 'revision', type=str, default='main',
                  help='Revision of repository.', show_default=True)
    @click.option('-a', '--archive_file', 'archive_file', type=str, required=True,
                  help='Archive file in repository.', show_default=True)
    @click.option('-i', '--idx_file', 'idx_file', type=str, default=None,
                  help='', show_default=True)
    @click.option('-l', '--list', 'show_detailed', is_flag=True, type=bool, default=False,
                  help='Show detailed file information.', show_default=True)
    @click.option('-s', '--sort_by', 'sort_by', type=click.Choice(['offset', 'name', 'size']), default='offset',
                  help='Sort order of files.', show_default=True)
    @click.option('-o', '--order_by', 'order_by', type=click.Choice(['asc', 'desc']), default='asc',
                  help='Order of the mentioned sorting.', show_default=True)
    @click.option('-I', '--information', 'show_information', type=bool, is_flag=True, default=False,
                  help='Show information of index file.', show_default=True)
    def ls(repo_id: str, idx_repo_id: Optional[str], repo_type: RepoTypeTyping, revision: str,
           show_detailed: bool, show_information: bool,
           sort_by: Literal['offset', 'name', 'size'], order_by: Literal['asc', 'desc'],
           archive_file: str, idx_file: Optional[str] = None):
        """
        List files from a HuggingFace repository's index tar file.

        This function retrieves and displays information about files in a HuggingFace
        repository's index tar file. It can show detailed file information, repository
        statistics, and allows for sorting and filtering of the file list.

        :param repo_id: The ID of the HuggingFace repository.
        :type repo_id: str
        :param idx_repo_id: The ID of the index repository (if different from repo_id).
        :type idx_repo_id: Optional[str]
        :param repo_type: The type of the HuggingFace repository (e.g., 'dataset', 'model').
        :type repo_type: RepoTypeTyping
        :param revision: The revision of the repository to use.
        :type revision: str
        :param show_detailed: Flag to show detailed file information.
        :type show_detailed: bool
        :param show_information: Flag to show general information about the index file.
        :type show_information: bool
        :param sort_by: Criterion to sort the files by ('offset', 'name', or 'size').
        :type sort_by: Literal['offset', 'name', 'size']
        :param order_by: Order of sorting ('asc' or 'desc').
        :type order_by: Literal['asc', 'desc']
        :param archive_file: The name of the archive file in the repository.
        :type archive_file: str
        :param idx_file: The name of the index file (if different from default).
        :type idx_file: Optional[str]

        :return: None

        This function performs the following steps:

        1. Configures the HTTP backend for HuggingFace Hub.
        2. Retrieves the index information for the specified repository and archive.
        3. If show_information is True, displays general statistics about the repository and files.
        4. If not showing information, lists the files according to the specified sorting and filtering options.

        The function uses click styles to format the output for better readability in the terminal.
        """
        configure_http_backend(get_requests_session)

        idx_info = hf_tar_get_index(
            repo_id=repo_id,
            repo_type=repo_type,
            revision=revision,
            archive_in_repo=archive_file,

            idx_repo_id=idx_repo_id or repo_id,
            idx_repo_type=repo_type,
            idx_revision=revision,
            idx_file_in_repo=idx_file,
        )
        if show_information:
            print('Repo ID: ' + click.style(repo_id, underline=True, fg='blue'))
            if idx_repo_id:
                print('Index Repo ID: ' + click.style(idx_repo_id, underline=True, fg='blue'))
            print('Repo Type: ' + click.style(repo_type, underline=True, fg='blue'))
            print('Revision: ' + click.style(revision, underline=True, fg='blue'))
            print('Archive File: ' + click.style(archive_file, underline=True, fg='blue'))
            if idx_file:
                print('Index File: ' + click.style(idx_file, underline=True, fg='blue'))
            print()

            print('File Size: ' + click.style(size_to_bytes_str(idx_info['filesize'], precision=3), fg='blue')
                  + ' (' + click.style(plural_word(idx_info['filesize'], "Byte"), underline=True) + ')')
            print('Native Hash: ' + click.style(idx_info['hash'], underline=True))
            print('LFS Hash: ' + click.style(idx_info['hash_lfs'], underline=True))
            print('Files: ' + click.style(plural_word(len(idx_info['files']), 'file'), underline=True, fg='blue'))
            if idx_info['files']:
                d_files = {}
                for file in idx_info['files'].keys():
                    type_ = get_file_type(file)
                    d_files[type_] = d_files.get(type_, 0) + 1
                for type_, type_name in _FT_NAME_MAP.items():
                    if d_files.get(type_, 0) > 0:
                        print(f'  {titleize(type_name)} Files: '
                              + click.style(plural_word(d_files[type_], "file"), underline=True))
                        pass

                d_exts = {}
                for file in idx_info['files'].keys():
                    _, ext = os.path.splitext(file)
                    d_exts[ext] = d_exts.get(ext, 0) + 1
                print('File Extensions:')
                for ext, count in sorted(d_exts.items(), key=lambda x: (-x[1], x[0])):
                    print(f'  {ext or "<none>"} : ' + click.style(plural_word(count, "file"), underline=True))

                # Convert to numpy array for easier calculations
                file_sizes = [file_info['size'] for file, file_info in idx_info['files'].items()]

                # Basic statistics
                total_size = sum(file_sizes)
                mean_size = statistics.mean(file_sizes)
                median_size = statistics.median(file_sizes)
                min_size = min(file_sizes)
                max_size = max(file_sizes)

                # Quartiles
                sorted_sizes = sorted(file_sizes)
                n = len(sorted_sizes)
                q1 = sorted_sizes[n // 4]
                q3 = sorted_sizes[(3 * n) // 4]
                iqr = q3 - q1
                std_dev = statistics.stdev(file_sizes)

                with warnings.catch_warnings():
                    warnings.simplefilter("ignore", UserWarning)
                    print(f"Total Size: " +
                          click.style(size_to_bytes_str(total_size, precision=3), underline=True, fg='blue'))
                    print(f"  Average File Size: " +
                          click.style(size_to_bytes_str(mean_size, precision=3), underline=True, fg='blue'))
                    print(f"  Median File Size: " +
                          click.style(size_to_bytes_str(median_size, precision=3), underline=True, fg='blue'))
                    print(f"  Smallest File Size: " +
                          click.style(size_to_bytes_str(min_size, precision=3), underline=True))
                    print(f"  Largest File Size: " +
                          click.style(size_to_bytes_str(max_size, precision=3), underline=True))
                    print(f"  Standard Deviation: " +
                          click.style(size_to_bytes_str(std_dev, precision=3), underline=True))
                    print("Quartiles:")
                    print(f"  Q1 (25th Percentile): {size_to_bytes_str(q1, precision=3)}")
                    print(f"  Q2 (50th Percentile, Median): {size_to_bytes_str(median_size, precision=3)}")
                    print(f"  Q3 (75th Percentile): {size_to_bytes_str(q3, precision=3)}")
                    print(f"  Interquartile Range (IQR): {size_to_bytes_str(iqr, precision=3)}")
            print()

            is_ready = hf_tar_validate(
                repo_id=repo_id,
                repo_type=repo_type,
                revision=revision,
                archive_in_repo=archive_file,

                idx_repo_id=idx_repo_id or repo_id,
                idx_repo_type=repo_type,
                idx_revision=revision,
                idx_file_in_repo=idx_file,
            )

            print('Status: ' + (
                click.style('Up-To-Date', fg='green', underline=True) if is_ready else
                click.style('Outdated', fg='yellow', underline=True)
            ))
            if not is_ready:
                print('Index file is recommended to get refreshed.')

        else:
            rows = []
            for file, file_info in sorted(idx_info['files'].items(), key=lambda x: (x[1]['offset'], x[0])):
                rows.append({
                    'file': hf_normpath(file),
                    'offset': file_info['offset'],
                    'size': file_info['size'],

                    't_file': str(file),
                    't_offset': str(file_info['offset']),
                    't_size': plural_word(file_info['size'], "Byte"),
                    't_size_text': size_to_bytes_str(file_info['size'], precision=3),
                    't_sha256': file_info['sha256'],
                })
            if sort_by == 'offset':
                rows = sorted(rows, key=lambda x: (x['offset'], x['file']), reverse=(order_by != 'asc'))
            elif sort_by == 'name':
                rows = sorted(rows, key=lambda x: (x['file'], x['offset']), reverse=(order_by != 'asc'))
            elif sort_by == 'size':
                rows = sorted(rows, key=lambda x: (x['size'], x['offset'], x['file']), reverse=(order_by != 'asc'))
            else:
                raise ValueError(f'Unknown sort_by {sort_by!r}.')  # pragma: no cover

            if len(rows):
                if show_detailed:
                    max_t_file_len = max(len(row['t_file']) for row in rows)
                    max_t_offset_len = max(len(row['t_offset']) for row in rows)
                    max_t_size_text_len = max(len(row['t_size_text']) for row in rows)
                    max_t_sha256_len = max(len(row['t_sha256']) for row in rows)

                    for row in rows:
                        print(' ' * (max_t_offset_len - len(row['t_offset'])) + row['t_offset'], end=' | ')
                        fc = get_file_type(row['t_file'])
                        print(' ' * (max_t_file_len - len(row['t_file']))
                              + click.style(row['t_file'], fg=fc.render_color), end=' ')
                        print(' ' * (max_t_size_text_len - len(row['t_size_text']))
                              + click.style(row['t_size_text'], underline=True), end=' ')
                        print(' ' * (max_t_sha256_len - len(row['t_sha256']))
                              + click.style(row['t_sha256']))

                else:
                    for row in rows:
                        file = row['file']
                        fc = get_file_type(file)
                        print(click.style(file, fg=fc.render_color))

    return cli

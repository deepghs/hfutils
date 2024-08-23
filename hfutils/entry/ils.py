import os.path
import warnings
from typing import Optional, Literal

import click
import numpy as np
import pandas as pd
from hbutils.scale import size_to_bytes_str
from hbutils.string import plural_word, titleize
from huggingface_hub import configure_http_backend

from .base import CONTEXT_SETTINGS
from ..index import hf_tar_get_index
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
            print('Repo ID: ' + click.style(repo_id, underline=True))
            if idx_repo_id:
                print('Index Repo ID: ' + click.style(idx_repo_id, underline=True))
            print('Repo Type: ' + click.style(repo_type, underline=True))
            print('Revision: ' + click.style(revision, underline=True))
            print('Archive File: ' + click.style(archive_file, underline=True))
            if idx_file:
                print('Index File: ' + click.style(idx_file, underline=True))
            print()

            print('File Size: ' + click.style(size_to_bytes_str(idx_info['filesize'], precision=3))
                  + ' (' + click.style(plural_word(idx_info['filesize'], "Byte"), underline=True) + ')')
            print('Native Hash: ' + click.style(idx_info['hash'], underline=True))
            print('LFS Hash: ' + click.style(idx_info['hash_lfs'], underline=True))
            print('Files: ' + click.style(plural_word(len(idx_info['files']), 'file'), underline=True))
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
                sizes = np.array(file_sizes)

                # Basic statistics
                total_files = len(sizes)
                total_size = np.sum(sizes)
                mean_size = np.mean(sizes)
                median_size = np.median(sizes)
                min_size = np.min(sizes)
                max_size = np.max(sizes)

                # Quartiles
                q1, q3 = np.percentile(sizes, [25, 75])
                iqr = q3 - q1
                std_dev = np.std(sizes)

                with warnings.catch_warnings():
                    warnings.simplefilter("ignore", UserWarning)
                    print(f"Total Size: {size_to_bytes_str(total_size.item(), precision=3)}")
                    print(f"  Average File Size: {size_to_bytes_str(mean_size.item(), precision=3)}")
                    print(f"  Median File Size: {size_to_bytes_str(median_size.item(), precision=3)}")
                    print(f"  Smallest File Size: {size_to_bytes_str(min_size.item(), precision=3)}")
                    print(f"  Largest File Size: {size_to_bytes_str(max_size.item(), precision=3)}")
                    print(f"  Standard Deviation: {size_to_bytes_str(std_dev.item(), precision=3)}")
                    print("Quartiles:")
                    print(f"  Q1 (25th Percentile): {size_to_bytes_str(q1.item(), precision=3)}")
                    print(f"  Q2 (50th Percentile, Median): {size_to_bytes_str(median_size.item(), precision=3)}")
                    print(f"  Q3 (75th Percentile): {size_to_bytes_str(q3.item(), precision=3)}")
                    print(f"  Interquartile Range (IQR): {size_to_bytes_str(iqr.item(), precision=3)}")

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
            df = pd.DataFrame(rows)
            if sort_by == 'offset':
                df = df.sort_values(by=['offset', 'file'], ascending=order_by == 'asc')
            elif sort_by == 'name':
                df = df.sort_values(by=['file', 'offset'], ascending=order_by == 'asc')
            elif sort_by == 'size':
                df = df.sort_values(by=['size', 'offset', 'file'], ascending=order_by == 'asc')
            else:
                raise ValueError(f'Unknown sort_by {sort_by!r}.')  # pragma: no cover

            if len(df):
                if show_detailed:
                    max_t_file_len = df['t_file'].map(len).max().item()
                    max_t_offset_len = df['t_offset'].map(len).max().item()
                    max_t_size_len = df['t_size'].map(len).max().item()
                    max_t_size_text_len = df['t_size_text'].map(len).max().item()
                    max_t_sha256_len = df['t_sha256'].map(len).max().item()

                    for row in df.to_dict('records'):
                        print(' ' * (max_t_offset_len - len(row['t_offset'])) + row['t_offset'], end='')
                        print(' | ', end='')

                        fc = get_file_type(row['t_file'])
                        print(' ' * (max_t_file_len - len(row['t_file']))
                              + click.style(row['t_file'], fg=fc.render_color), end=' ')

                        print(' ' * (max_t_size_text_len - len(row['t_size_text']))
                              + click.style(row['t_size_text'], underline=True), end=' ')
                        print(' ' * (max_t_sha256_len - len(row['t_sha256']))
                              + click.style(row['t_sha256']))

                else:
                    for file in df['t_file']:
                        fc = get_file_type(file)
                        print(click.style(file, fg=fc.render_color))

    return cli

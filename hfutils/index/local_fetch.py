import json
import os
from typing import Optional, List


def tar_get_index(archive_file: str, idx_file: Optional[str] = None):
    body, _ = os.path.splitext(archive_file)
    default_index_file = f'{body}.json'
    with open(idx_file or default_index_file, 'r') as f:
        return json.load(f)


def tar_list_files(archive_file: str, idx_file: Optional[str] = None) -> List[str]:
    index_data = tar_get_index(
        archive_file=archive_file,
        idx_file=idx_file,
    )
    return list(index_data['files'].keys())


def tar_file_exists(archive_file: str, file_in_archive: str, idx_file: Optional[str] = None) -> bool:
    from .fetch import _hf_files_process, _n_path
    index = tar_get_index(
        archive_file=archive_file,
        idx_file=idx_file,
    )
    files = _hf_files_process(index['files'])
    return _n_path(file_in_archive) in files


def tar_file_info(archive_file: str, file_in_archive: str, idx_file: Optional[str] = None) -> dict:
    from .fetch import _hf_files_process, _n_path
    index = tar_get_index(
        archive_file=archive_file,
        idx_file=idx_file,
    )
    files = _hf_files_process(index['files'])
    if _n_path(file_in_archive) not in files:
        raise FileNotFoundError(f'File {file_in_archive!r} not found '
                                f'in local archive {archive_file!r}.')
    else:
        return files[_n_path(file_in_archive)]


def tar_file_size(archive_file: str, file_in_archive: str, idx_file: Optional[str] = None) -> int:
    return tar_file_info(
        archive_file=archive_file,
        file_in_archive=file_in_archive,
        idx_file=idx_file,
    )['size']


def tar_file_download(archive_file: str, file_in_archive: str, local_file: str,
                      idx_file: Optional[str] = None, chunk_size: int = 1 << 20):
    from .fetch import _hf_files_process, _n_path, _f_sha256, \
        ArchiveStandaloneFileIncompleteDownload, ArchiveStandaloneFileHashNotMatch

    index = tar_get_index(
        archive_file=archive_file,
        idx_file=idx_file,
    )
    files = _hf_files_process(index['files'])
    if _n_path(file_in_archive) not in files:
        raise FileNotFoundError(f'File {file_in_archive!r} not found '
                                f'in local archive {archive_file!r}.')

    info = files[_n_path(file_in_archive)]

    if os.path.dirname(local_file):
        os.makedirs(os.path.dirname(local_file), exist_ok=True)
    try:
        with open(local_file, 'wb') as wf:
            if info['size'] > 0:
                with open(archive_file, 'rb') as rf:
                    rf.seek(info['offset'])
                    tp = info['offset'] + info['size']
                    while rf.tell() < tp:
                        read_bytes = min(tp - rf.tell(), chunk_size)
                        wf.write(rf.read(read_bytes))

        if os.path.getsize(local_file) != info['size']:
            raise ArchiveStandaloneFileIncompleteDownload(
                f'Expected size is {info["size"]}, but actually {os.path.getsize(local_file)} downloaded.'
            )

        if info.get('sha256'):
            _sha256 = _f_sha256(local_file)
            if _sha256 != info['sha256']:
                raise ArchiveStandaloneFileHashNotMatch(
                    f'Expected hash is {info["sha256"]!r}, but actually {_sha256!r} found.'
                )

    except Exception:
        if os.path.exists(local_file):
            os.remove(local_file)
        raise

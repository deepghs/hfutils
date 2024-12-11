import os.path
from collections.abc import Sequence
from dataclasses import dataclass
from operator import itemgetter
from typing import Optional, List, Literal, Tuple

from hbutils.scale import size_to_bytes_str
from hbutils.string import plural_word, format_tree
from huggingface_hub.hf_api import RepoFile

from ..operate import list_all_with_pattern
from ..operate.base import RepoTypeTyping
from ..utils import hf_normpath, hf_fs_path


@dataclass
class RepoFileItem:
    path: str
    size: int
    is_lfs: bool
    lfs_sha256: Optional[str]
    blob_id: str

    @classmethod
    def from_repo_file(cls, repo_file: RepoFile, subdir: str = '') -> 'RepoFileItem':
        subdir = subdir or '.'
        return cls(
            path=hf_normpath(os.path.relpath(repo_file.path, subdir)),
            size=repo_file.lfs.size if repo_file.lfs else repo_file.size,
            is_lfs=bool(repo_file.lfs),
            lfs_sha256=repo_file.lfs.sha256 if repo_file.lfs else None,
            blob_id=repo_file.blob_id,
        )

    @property
    def path_segments(self) -> Tuple[str, ...]:
        return tuple(seg for seg in self.path.split('/') if seg and seg != '.')

    def __repr__(self):
        return (f'<{self.__class__.__name__} {self.path}, size: {size_to_bytes_str(self.size, sigfigs=3, system="si")}'
                f'{" (LFS)" if self.is_lfs else ""}>')


class RepoFileList(Sequence):
    def __init__(self, repo_id: str, items: List[RepoFileItem],
                 repo_type: RepoTypeTyping = 'dataset', revision: str = 'main', subdir: Optional[str] = ''):
        self.repo_id = repo_id
        self.repo_type = repo_type
        self.revision = revision
        self.subdir = hf_normpath(subdir or '.')
        self._file_items = list(items)
        self._total_size = 0
        for item in self._file_items:
            self._total_size += item.size

    def __getitem__(self, index):
        return self._file_items[index]

    def __len__(self) -> int:
        return len(self._file_items)

    @property
    def total_size(self) -> int:
        return self._total_size

    def _tree(self, max_items: Optional[int] = 10):
        title = hf_fs_path(
            repo_id=self.repo_id,
            repo_type=self.repo_type,
            revision=self.revision,
            filename=self.subdir,
        )
        return (
            f'{title} ({plural_word(len(self._file_items), "file")}, '
            f'{size_to_bytes_str(self._total_size, sigfigs=3, system="si")})',
            [
                *(
                    (repr(item), []) for item in
                    (self._file_items[:max_items] if max_items and max_items > 0 else self._file_items)
                ),
                *(
                    [
                        (f'... ({plural_word(len(self._file_items), "file")}) in total ...', [])
                    ] if max_items and 0 < max_items < len(self._file_items) else []
                )
            ]
        )

    def __repr__(self):
        return format_tree(
            self._tree(),
            format_node=itemgetter(0),
            get_children=itemgetter(1),
        )

    def repr(self, max_items: Optional[int] = 10):
        return format_tree(
            self._tree(max_items=max_items),
            format_node=itemgetter(0),
            get_children=itemgetter(1),
        )


SortByTyping = Literal['none', 'path', 'size']


def hf_hub_repo_analysis(
        repo_id: str, pattern: str = '**/*', repo_type: RepoTypeTyping = 'dataset',
        revision: str = 'main', hf_token: Optional[str] = None, silent: bool = False,
        subdir: str = '', sort_by: SortByTyping = 'path', **kwargs,
) -> RepoFileList:
    if subdir and subdir != '.':
        pattern = f'{subdir}/{pattern}'

    file_items = []
    for item in list_all_with_pattern(
            repo_id=repo_id,
            repo_type=repo_type,
            revision=revision,
            pattern=pattern,
            hf_token=hf_token,
            silent=silent,
            **kwargs
    ):
        if isinstance(item, RepoFile):
            file_items.append(RepoFileItem.from_repo_file(item, subdir))

    if sort_by != 'none':
        file_items = sorted(file_items,
                            key=lambda x: x.path_segments if sort_by == 'path' else (-x.size, x.path_segments))

    return RepoFileList(
        repo_id=repo_id,
        repo_type=repo_type,
        revision=revision,
        subdir=subdir,
        items=file_items
    )

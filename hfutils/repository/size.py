from collections.abc import Sequence
from typing import Optional, List

from huggingface_hub.hf_api import RepoFile

from ..operate import list_all_with_pattern
from ..operate.base import RepoTypeTyping
from ..utils import hf_normpath


class RepoFileItem:
    def __init__(self, repo_file: RepoFile):
        self.file: RepoFile = repo_file

    @property
    def size(self) -> int:
        return self.file.lfs.size if self.file.lfs else self.file.size

    @property
    def is_lfs(self) -> bool:
        return bool(self.file.lfs)

    @property
    def lfs_sha256(self) -> Optional[str]:
        return self.file.lfs.sha256 if self.file.lfs else None

    @property
    def blob_id(self) -> str:
        return self.file.blob_id

    @property
    def path(self) -> str:
        return hf_normpath(self.file.path)

    def _value(self):
        return self.size, self.is_lfs, self.lfs_sha256, self.blob_id, self.path

    def __eq__(self, other):
        return isinstance(other, RepoFileItem) and self._value() == other._value()


class RepoFileList(Sequence[RepoFileItem]):
    def __init__(self, repo_id: str, items: List[RepoFileItem],
                 repo_type: RepoTypeTyping = 'dataset', revision: str = 'main'):
        self.repo_id = repo_id
        self.repo_type = repo_type
        self.revision = revision
        self._file_items = list(items)
        self._total_size = 0
        for item in self._file_items:
            self._total_size += item.size

    def __getitem__(self, index):
        return self._file_items[index]

    def __len__(self) -> int:
        return len(self._file_items)


def hf_hub_repo_analysis(
        repo_id: str, pattern: str = '**/*', repo_type: RepoTypeTyping = 'dataset',
        revision: str = 'main', hf_token: Optional[str] = None, silent: bool = False,
        subdir: str = '', **kwargs,
) -> RepoFileList:
    if subdir and subdir != '.':
        pattern = f'{subdir}/{pattern}'

    result = []
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
            result.append(RepoFileItem(item))

    return RepoFileList(
        repo_id=repo_id,
        repo_type=repo_type,
        revision=revision,
        items=result
    )

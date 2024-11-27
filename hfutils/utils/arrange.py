import os
import pathlib
from collections import defaultdict
from dataclasses import dataclass
from typing import List, Union, Optional

from natsort import natsorted

from .heap import Heap
from .walk import walk_files


@dataclass
class FileItem:
    file: str
    size: int
    count: int

    @classmethod
    def from_file(cls, file: str, rel_to: Optional[str] = None) -> 'FileItem':
        file = pathlib.Path(file).resolve(strict=True)
        size = os.path.getsize(str(file))
        if rel_to:
            rel_to = pathlib.Path(rel_to).resolve(strict=True)
            file = file.relative_to(rel_to)

        return cls(
            file=str(file),
            size=size,
            count=1,
        )


@dataclass
class FilesGroup:
    files: List[str]
    size: int
    count: int

    @classmethod
    def new(cls) -> 'FilesGroup':
        return cls(
            files=[],
            size=0,
            count=0,
        )

    def add(self, file: Union[FileItem, 'FilesGroup']) -> 'FilesGroup':
        if isinstance(file, FileItem):
            self.files.append(file.file)
            self.size += file.size
            self.count += file.count
        elif isinstance(file, FilesGroup):
            self.files.extend(file.files)
            self.size += file.size
            self.count += file.count
        else:
            raise TypeError(f'Unknown type {type(file)!r} to add - {file!r}.')

        return self


def _group_by_default(files: List[FileItem]) -> List[Union[FileItem, FilesGroup]]:
    return files


def _group_by_segs(files: List[FileItem], segs: int) -> List[Union[FileItem, FilesGroup]]:
    d = defaultdict(FilesGroup.new)
    for file in files:
        d[pathlib.Path(file.file).parts[:segs]].add(file)

    retval = []
    for key, value in natsorted(d.items()):
        retval.append(value)
    return retval


def _group_by(files: List[FileItem], group_method: Optional[Union[str, int]] = None) \
        -> List[Union[FileItem, FilesGroup]]:
    if isinstance(group_method, int):
        pass  # is an int
    elif isinstance(group_method, str):
        try:
            group_method = int(group_method)
        except (TypeError, ValueError):
            pass  # is a str
    elif isinstance(group_method, type(None)):
        pass  # default policy
    else:
        raise TypeError(f'Unknown group by method - {group_method!r}.')

    if isinstance(group_method, int) and group_method == 0:
        raise ValueError('Unable to group by 0 segments.')

    if group_method is None:
        return _group_by_default(files)
    elif isinstance(group_method, int):
        return _group_by_segs(files, segs=group_method)
    else:
        raise ValueError(f'Unsupported group by method - {group_method!r}.')


def walk_files_with_groups(directory: str, pattern: Optional[str] = None,
                           group_method: Optional[Union[str, int]] = None,
                           max_total_size: Optional[float] = None) \
        -> List[FilesGroup]:
    all_items = [
        FileItem.from_file(os.path.join(directory, file), rel_to=directory)
        for file in walk_files(directory, pattern=pattern)
    ]
    if max_total_size is None:
        final_group = FilesGroup.new()
        for file_item in all_items:
            final_group.add(file_item)
        return [final_group]

    else:
        raw_groups: List[Union[FileItem, FilesGroup]] = _group_by(all_items, group_method=group_method)
        collected_groups: List[FilesGroup] = []
        heap: Heap[FilesGroup] = Heap(key=lambda x: (x.size, x.count))
        for group in raw_groups:
            if not heap or (heap.peek().size + group.size) > max_total_size:
                new_group = FilesGroup.new()
                heap.push(new_group)
                collected_groups.append(new_group)
            item = heap.pop()
            item.add(group)
            heap.push(item)

        collected_groups = [item for item in collected_groups if item.count > 0]
        return collected_groups

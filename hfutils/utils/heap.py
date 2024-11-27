import heapq
from dataclasses import dataclass
from functools import total_ordering
from typing import List, Generic, TypeVar, Callable, Any, Optional, Iterable

T = TypeVar('T')


@total_ordering
@dataclass
class HeapItem(Generic[T]):
    item: T
    key_func: Callable[[T], Any]
    reverse: bool = False

    def __lt__(self, other: 'HeapItem') -> bool:
        if self.reverse:
            return self.key_func(self.item) > self.key_func(other.item)
        return self.key_func(self.item) < self.key_func(other.item)

    def __eq__(self, other: 'HeapItem') -> bool:
        return self.key_func(self.item) == self.key_func(other.item)


class Heap(Generic[T]):
    def __init__(self, items: Optional[Iterable[T]] = None, *,
                 key: Optional[Callable[[T], Any]] = None, reverse: bool = False):
        self._key = key if key is not None else lambda x: x
        self._reverse = reverse
        if items is not None:
            self._heap = [self._new(item) for item in items]
            heapq.heapify(self._heap)
        else:
            self._heap: List[HeapItem[T]] = []

    def _new(self, item: T):
        return HeapItem(item, self._key, self._reverse)

    def push(self, item: T) -> None:
        heapq.heappush(self._heap, self._new(item))

    def pop(self) -> T:
        if not self._heap:
            raise IndexError('Pop from an empty heap')
        return heapq.heappop(self._heap).item

    def peek(self) -> T:
        if not self._heap:
            raise IndexError('Peek from an empty heap')
        return self._heap[0].item

    def __len__(self) -> int:
        return len(self._heap)

    def is_empty(self) -> bool:
        return len(self._heap) == 0

    def __bool__(self):
        return not self.is_empty()

    def __repr__(self):
        items = [item.item for item in self._heap]
        return f'{self.__class__.__name__}({items})'

"""
A generic heap implementation that supports custom comparison keys and reverse ordering.

The implementation uses Python's built-in heapq module internally while providing
a more convenient and feature-rich interface.
"""

import heapq
from dataclasses import dataclass
from functools import total_ordering
from typing import List, Generic, TypeVar, Callable, Any, Optional, Iterable

T = TypeVar('T')


@total_ordering
@dataclass
class HeapItem(Generic[T]):
    """
    A wrapper class for items stored in the heap that handles custom comparison logic.

    This class encapsulates an item along with its comparison logic, enabling custom
    key-based comparisons and reverse ordering in the heap.

    :param item: The actual item to be stored
    :type item: T
    :param key_func: Function to extract comparison key from the item
    :type key_func: Callable[[T], Any]
    :param reverse: Whether to reverse the comparison order
    :type reverse: bool

    :ivar item: The stored item
    :ivar key_func: The key extraction function
    :ivar reverse: The comparison order flag
    """

    item: T
    key_func: Callable[[T], Any]
    reverse: bool = False

    def __lt__(self, other: 'HeapItem') -> bool:
        """
        Compare two heap items for ordering.

        :param other: Another HeapItem to compare with
        :type other: HeapItem
        :return: True if this item is less than the other item
        :rtype: bool
        """
        if self.reverse:
            return self.key_func(self.item) > self.key_func(other.item)
        return self.key_func(self.item) < self.key_func(other.item)

    def __eq__(self, other: 'HeapItem') -> bool:
        """
        Check equality between two heap items.

        :param other: Another HeapItem to compare with
        :type other: HeapItem
        :return: True if items are equal based on their keys
        :rtype: bool
        """
        return self.key_func(self.item) == self.key_func(other.item)


class Heap(Generic[T]):
    """
    A generic heap implementation supporting custom key functions and reverse ordering.

    This heap can be used as either a min-heap or max-heap and supports custom
    key functions for comparison. It provides standard heap operations like
    push, pop, and peek.

    :param items: Optional initial items to populate the heap
    :type items: Optional[Iterable[T]]
    :param key: Optional function to extract comparison keys from items
    :type key: Optional[Callable[[T], Any]]
    :param reverse: Whether to use max-heap instead of min-heap ordering
    :type reverse: bool

    :example::
        >>> # Create a min-heap of numbers
        >>> heap = Heap([3, 1, 4, 1, 5])
        >>> # Create a max-heap of strings based on length
        >>> heap = Heap(['a', 'bbb', 'cc'], key=len, reverse=True)
    """

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
        """
        Create a new HeapItem wrapper for the given item.

        :param item: Item to wrap
        :type item: T
        :return: Wrapped heap item
        :rtype: HeapItem[T]
        """
        return HeapItem(item, self._key, self._reverse)

    def push(self, item: T) -> None:
        """
        Push an item onto the heap.

        :param item: Item to add to the heap
        :type item: T
        """
        heapq.heappush(self._heap, self._new(item))

    def pop(self) -> T:
        """
        Remove and return the top item from the heap.

        :return: The top item from the heap
        :rtype: T
        :raises IndexError: If the heap is empty
        """
        if not self._heap:
            raise IndexError('Pop from an empty heap')
        return heapq.heappop(self._heap).item

    def peek(self) -> T:
        """
        Return the top item from the heap without removing it.

        :return: The top item from the heap
        :rtype: T
        :raises IndexError: If the heap is empty
        """
        if not self._heap:
            raise IndexError('Peek from an empty heap')
        return self._heap[0].item

    def __len__(self) -> int:
        """
        Get the number of items in the heap.

        :return: Number of items in the heap
        :rtype: int
        """
        return len(self._heap)

    @property
    def is_empty(self) -> bool:
        """
        Check if the heap is empty.

        :return: True if the heap has no items, False otherwise
        :rtype: bool
        """
        return len(self._heap) == 0

    def __bool__(self):
        """
        Boolean representation of the heap.

        :return: True if the heap is not empty, False otherwise
        :rtype: bool
        """
        return not self.is_empty

    def __repr__(self):
        """
        Get a string representation of the heap.

        :return: String representation showing the heap's items
        :rtype: str
        """
        items = [item.item for item in self._heap]
        return f'{self.__class__.__name__}({items})'

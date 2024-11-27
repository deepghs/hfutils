from typing import NamedTuple

import pytest

from hfutils.utils import Heap
from hfutils.utils.heap import HeapItem


@pytest.fixture
def empty_heap():
    return Heap()


@pytest.fixture
def int_heap():
    return Heap([3, 1, 4, 1, 5, 9, 2, 6, 5, 3, 5])


@pytest.fixture
def str_heap():
    return Heap(['apple', 'banana', 'cherry'])


class Person(NamedTuple):
    name: str
    age: int


@pytest.fixture
def person_heap():
    people = [
        Person('Alice', 25),
        Person('Bob', 30),
        Person('Charlie', 20)
    ]
    return Heap(people, key=lambda x: x.age)


@pytest.mark.unittest
class TestHeap:
    def test_empty_heap_creation(self, empty_heap):
        assert len(empty_heap) == 0
        assert empty_heap.is_empty
        assert not empty_heap

    def test_heap_creation_with_items(self, int_heap):
        assert len(int_heap) == 11
        assert not int_heap.is_empty
        assert int_heap

    def test_push_and_pop_integers(self, empty_heap):
        empty_heap.push(5)
        empty_heap.push(3)
        empty_heap.push(7)
        assert empty_heap.pop() == 3
        assert empty_heap.pop() == 5
        assert empty_heap.pop() == 7

    def test_push_and_pop_strings(self, str_heap):
        assert str_heap.pop() == 'apple'
        assert str_heap.pop() == 'banana'
        assert str_heap.pop() == 'cherry'

    def test_peek(self, int_heap):
        min_val = int_heap.peek()
        assert min_val == 1
        assert len(int_heap) == 11  # Length shouldn't change after peek

    def test_empty_heap_exceptions(self, empty_heap):
        with pytest.raises(IndexError):
            empty_heap.pop()
        with pytest.raises(IndexError):
            empty_heap.peek()

    def test_custom_key_function(self):
        heap = Heap([('a', 3), ('b', 1), ('c', 2)], key=lambda x: x[1])
        assert heap.pop() == ('b', 1)
        assert heap.pop() == ('c', 2)
        assert heap.pop() == ('a', 3)

    def test_reverse_heap(self):
        heap = Heap([1, 3, 2, 5, 4], reverse=True)
        assert heap.pop() == 5
        assert heap.pop() == 4
        assert heap.pop() == 3

    def test_person_objects(self, person_heap):
        assert person_heap.pop().age == 20
        assert person_heap.pop().age == 25
        assert person_heap.pop().age == 30

    def test_mixed_numbers(self):
        heap = Heap([3.14, 2, -1, 0.5])
        assert heap.pop() == -1
        assert heap.pop() == 0.5
        assert heap.pop() == 2

    def test_heap_representation(self, int_heap):
        assert repr(int_heap).startswith('Heap([')
        assert repr(int_heap).endswith('])')

    def test_tuple_comparison(self):
        heap = Heap([(1, 'a'), (2, 'b'), (0, 'c')])
        assert heap.pop() == (0, 'c')
        assert heap.pop() == (1, 'a')
        assert heap.pop() == (2, 'b')

    def test_custom_key_with_reverse(self):
        data = [{'id': 3}, {'id': 1}, {'id': 2}]
        heap = Heap(data, key=lambda x: x['id'], reverse=True)
        assert heap.pop()['id'] == 3
        assert heap.pop()['id'] == 2
        assert heap.pop()['id'] == 1

    def test_heap_item_equality(self):
        item1 = HeapItem(1, lambda x: x)
        item2 = HeapItem(1, lambda x: x)
        item3 = HeapItem(2, lambda x: x)
        assert item1 == item2
        assert item1 != item3

    def test_complex_objects(self):
        class Complex:
            def __init__(self, real):
                self.real = real

        heap = Heap([Complex(3), Complex(1), Complex(2)], key=lambda x: x.real)
        assert heap.pop().real == 1
        assert heap.pop().real == 2
        assert heap.pop().real == 3

    def test_string_key_function(self):
        heap = Heap(['aaa', 'a', 'aa'], key=len)
        assert heap.pop() == 'a'
        assert heap.pop() == 'aa'
        assert heap.pop() == 'aaa'

    def test_multiple_pushes(self, empty_heap):
        numbers = [4, 2, 6, 1, 3, 5]
        for num in numbers:
            empty_heap.push(num)
        result = []
        while not empty_heap.is_empty:
            result.append(empty_heap.pop())
        assert result == sorted(numbers)

    def test_heap_with_duplicates(self):
        heap = Heap([1, 1, 1, 2, 2, 3])
        result = []
        while not heap.is_empty:
            result.append(heap.pop())
        assert result == [1, 1, 1, 2, 2, 3]

    def test_custom_comparison_with_none(self):
        data = [{'value': 3}, {'value': None}, {'value': 1}]
        heap = Heap(data, key=lambda x: float('inf') if x['value'] is None else x['value'])
        assert heap.pop()['value'] == 1
        assert heap.pop()['value'] == 3
        assert heap.pop()['value'] is None

    def test_empty_initialization_with_key_and_reverse(self):
        heap = Heap(key=len, reverse=True)
        heap.push('a')
        heap.push('aaa')
        heap.push('aa')
        assert heap.pop() == 'aaa'
        assert heap.pop() == 'aa'
        assert heap.pop() == 'a'

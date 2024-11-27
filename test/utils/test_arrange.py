import os
import pathlib
import tempfile

import pytest
from hbutils.scale import size_to_bytes

from hfutils.utils import walk_files, FileItem, FilesGroup, walk_files_with_groups


# Fixtures
@pytest.fixture
def temp_directory():
    with tempfile.TemporaryDirectory() as tmpdirname:
        # Create some test files
        files = [
            'test1.txt',
            'test2.txt',
            'subdir/test3.txt',
            'subdir/test4.txt',
            'another/test5.txt'
        ]
        for file_path in files:
            full_path = os.path.join(tmpdirname, file_path)
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            with open(full_path, 'w') as f:
                f.write('test content')
        yield tmpdirname


@pytest.fixture
def sample_files(temp_directory):
    files = list(walk_files(temp_directory))
    return [FileItem.from_file(os.path.join(temp_directory, file), rel_to=temp_directory) for file in files]


@pytest.mark.unittest
class TestFileItem:
    def test_from_file(self, temp_directory):
        # Test FileItem.from_file method
        file_path = os.path.join(temp_directory, 'test1.txt')
        file_item = FileItem.from_file(file_path, rel_to=temp_directory)

        assert isinstance(file_item, FileItem)
        assert file_item.file == 'test1.txt'
        assert file_item.size > 0
        assert file_item.count == 1

    def test_from_file_absolute_path(self, temp_directory):
        # Test FileItem.from_file with absolute path
        file_path = os.path.join(temp_directory, 'test2.txt')
        file_item = FileItem.from_file(file_path)

        assert os.path.isabs(file_item.file)
        assert file_item.size > 0


@pytest.mark.unittest
class TestFilesGroup:
    def test_new_group(self):
        # Test FilesGroup.new method
        group = FilesGroup.new()

        assert group.files == []
        assert group.size == 0
        assert group.count == 0

    def test_add_file_item(self, sample_files):
        # Test adding FileItem to FilesGroup
        group = FilesGroup.new()
        group.add(sample_files[0])

        assert len(group.files) == 1
        assert group.size > 0
        assert group.count == 1

    def test_add_files_group(self, sample_files):
        # Test adding another FilesGroup
        group1 = FilesGroup.new()
        group1.add(sample_files[0])

        group2 = FilesGroup.new()
        group2.add(sample_files[1])

        group1.add(group2)

        assert len(group1.files) == 2
        assert group1.count == 2

    def test_add_invalid_type(self):
        # Test adding an invalid type raises TypeError
        group = FilesGroup.new()
        with pytest.raises(TypeError):
            group.add("invalid")


@pytest.mark.unittest
class TestGroupBy:
    def test_group_by_default(self, sample_files):
        # Test default grouping
        from hfutils.utils.arrange import _group_by_default
        groups = _group_by_default(sample_files)

        assert len(groups) == len(sample_files)
        assert all(isinstance(g, FileItem) for g in groups)

    def test_group_by_segs(self, sample_files):
        # Test grouping by path segments
        from hfutils.utils.arrange import _group_by_segs
        groups = _group_by_segs(sample_files, segs=1)

        assert len(groups) > 0
        assert all(isinstance(g, FilesGroup) for g in groups)

    def test_group_by_method(self, sample_files):
        # Test different group by methods
        from hfutils.utils.arrange import _group_by

        # Default grouping
        default_groups = _group_by(sample_files)
        assert len(default_groups) == len(sample_files)

        # Segment grouping
        seg_groups = _group_by(sample_files, 1)
        assert len(seg_groups) > 0

    def test_group_by_invalid_method(self, sample_files):
        # Test invalid group by methods
        from hfutils.utils.arrange import _group_by

        with pytest.raises(TypeError):
            _group_by(sample_files, (1, 2))

        with pytest.raises(ValueError):
            _group_by(sample_files, "invalid")

        with pytest.raises(ValueError):
            _group_by(sample_files, 0)


@pytest.mark.unittest
class TestWalkFilesWithGroups:
    def test_walk_files_with_groups_no_max_size(self, temp_directory):
        # Test walk_files_with_groups without max total size
        result = walk_files_with_groups(temp_directory)

        assert len(result) == 1
        assert result[0].count > 0
        assert result[0].size > 0

    def test_walk_files_with_groups_with_max_size(self, temp_directory):
        # Test walk_files_with_groups with max total size
        result = walk_files_with_groups(temp_directory, max_total_size=1000, group_method=1)

        assert len(result) > 0
        assert all(group.size <= 1000 for group in result)

    def test_walk_files_with_groups_pattern(self, temp_directory):
        # Test walk_files_with_groups with file pattern
        result = walk_files_with_groups(temp_directory, pattern='*.txt')

        assert len(result) == 1
        assert result[0].count > 0


# Fixtures
@pytest.fixture
def complex_directory():
    with tempfile.TemporaryDirectory() as tmpdirname:
        # Create a complex directory structure with files of different sizes
        file_structure = {
            'small': [
                ('root_small1.txt', 100),
                ('root_small2.txt', 200),
                ('folder1/small1.txt', 150),
                ('folder1/small2.txt', 250),
                ('folder2/small1.txt', 180),
            ],
            'medium': [
                ('folder1/medium1.dat', 1024),
                ('folder2/subfolder1/medium1.dat', 1500),
                ('folder2/subfolder1/medium2.dat', 2048),
                ('folder3/medium1.dat', 1800),
            ],
            'large': [
                ('folder1/large1.bin', 5000),
                ('folder2/subfolder2/large1.bin', 6000),
                ('folder3/subfolder1/large1.bin', 7000),
                ('folder3/subfolder1/subfolder1/large1.bin', 8000),
            ],
            'mixed': [
                ('mixed/a1/file1.txt', 100),
                ('mixed/a1/file2.dat', 1024),
                ('mixed/a2/file1.txt', 200),
                ('mixed/a2/subdir/file1.bin', 5000),
                ('mixed/a3/deep/path/file1.txt', 150),
            ]
        }

        # Create all directories and files
        for category in file_structure.values():
            for file_path, size in category:
                full_path = os.path.join(tmpdirname, file_path)
                os.makedirs(os.path.dirname(full_path), exist_ok=True)

                # Create file with specified size
                with open(full_path, 'wb') as f:
                    f.write(os.urandom(size))

        yield tmpdirname


@pytest.fixture
def complex_files(complex_directory):
    files = list(walk_files(complex_directory))
    return [FileItem.from_file(os.path.join(complex_directory, file), rel_to=complex_directory)
            for file in files]


@pytest.mark.unittest
class TestWalkFilesWithGroupsComplex:
    def test_group_by_size_threshold(self, complex_directory):
        # Test grouping with size threshold around 5000 bytes
        # Should separate large files from medium and small ones
        result = walk_files_with_groups(complex_directory, max_total_size=5000)

        assert len(result) > 1  # Should have multiple groups due to size limit
        assert all(group.size <= 5000 or group.count == 1 for group in result)

        # Verify total file count
        total_files = sum(group.count for group in result)
        original_files = len(list(walk_files(complex_directory)))
        assert total_files == original_files

    def test_group_by_size_threshold_size_str(self, complex_directory):
        # Test grouping with size threshold around 5000 bytes
        # Should separate large files from medium and small ones
        result = walk_files_with_groups(complex_directory, max_total_size='5kb')

        assert len(result) > 1  # Should have multiple groups due to size limit
        assert all(group.size <= size_to_bytes('5kb') or group.count == 1 for group in result)

        # Verify total file count
        total_files = sum(group.count for group in result)
        original_files = len(list(walk_files(complex_directory)))
        assert total_files == original_files

    def test_group_by_directory_depth(self, complex_directory):
        # Test grouping by directory depth (2 levels)
        result = walk_files_with_groups(complex_directory, group_method=2, max_total_size=10000)

        assert len(result) > 1  # Should have multiple groups due to size limit
        total_files = sum(group.count for group in result)
        original_files = len(list(walk_files(complex_directory)))
        assert total_files == original_files

        # Check if files are grouped by their directory structure
        dir_maps = {}
        for group in result:
            for filename in group.files:
                tk = pathlib.Path(filename).parts[:2]
                if tk not in dir_maps:
                    dir_maps[tk] = group
                else:
                    assert dir_maps[tk] is group

    def test_group_with_pattern_filtering(self, complex_directory):
        # Test grouping with specific file patterns
        txt_results = walk_files_with_groups(complex_directory, pattern="*.txt", max_total_size=1000)
        dat_results = walk_files_with_groups(complex_directory, pattern="*.dat", max_total_size=2000)
        bin_results = walk_files_with_groups(complex_directory, pattern="*.bin", max_total_size=8000)

        # Verify file extensions in each group
        for group in txt_results:
            assert all(f.endswith('.txt') for f in group.files)

        for group in dat_results:
            assert all(f.endswith('.dat') for f in group.files)

        for group in bin_results:
            assert all(f.endswith('.bin') for f in group.files)

    def test_balanced_grouping(self, complex_directory):
        # Test if grouping creates relatively balanced groups
        max_size = 10000
        result = walk_files_with_groups(complex_directory, max_total_size=max_size)

        # Calculate size distribution
        sizes = [group.size for group in result]
        avg_size = sum(sizes) / len(sizes)

        # Verify that no group is too small (less than 30% of max) unless it's necessary
        small_groups = [size for size in sizes if size < max_size * 0.3]
        # Allow only one small group (might be the last one)
        assert len(small_groups) <= 1

        # Verify that groups are relatively balanced
        assert all(size <= max_size for size in sizes)
        assert all(size >= avg_size * 0.3 for size in sizes[:-1])  # Exclude last group

    def test_deep_directory_structure(self, complex_directory):
        # Test handling of deep directory structures
        result = walk_files_with_groups(complex_directory, group_method=-2, max_total_size=15000)

        assert len(result) > 1  # Should have multiple groups due to size limit
        total_files = sum(group.count for group in result)
        original_files = len(list(walk_files(complex_directory)))
        assert total_files == original_files

        # Check if files are grouped by their directory structure
        dir_maps = {}
        for group in result:
            for filename in group.files:
                tk = pathlib.Path(filename).parts[:-2]
                if tk not in dir_maps:
                    dir_maps[tk] = group
                else:
                    assert dir_maps[tk] is group

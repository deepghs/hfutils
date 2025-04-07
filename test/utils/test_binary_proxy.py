from io import BytesIO, UnsupportedOperation
from unittest.mock import MagicMock

import pytest
from hbutils.testing import isolated_directory

from hfutils.utils import BinaryProxyIO


@pytest.fixture
def mock_stream():
    return MagicMock()


@pytest.fixture
def proxy_io(mock_stream):
    return BinaryProxyIO(mock_stream)


@pytest.fixture
def bytes_io():
    return BytesIO()


@pytest.mark.unittest
class TestBinaryProxyIO:
    def test_init(self, proxy_io):
        assert not proxy_io._closed
        assert proxy_io._pos == 0

    def test_enter(self, proxy_io):
        with proxy_io as p:
            assert p == proxy_io

    def test_enter_closed(self, proxy_io):
        proxy_io.close()
        with pytest.raises(ValueError, match="I/O operation on closed file."):
            with proxy_io:
                pass

    def test_close(self, proxy_io):
        proxy_io.close()
        assert proxy_io._closed

    def test_fileno(self, proxy_io):
        with pytest.raises(UnsupportedOperation):
            proxy_io.fileno()

    def test_flush(self, proxy_io):
        with pytest.raises(UnsupportedOperation):
            proxy_io.flush()

    def test_isatty(self, proxy_io):
        assert not proxy_io.isatty()

    def test_read(self, proxy_io):
        with pytest.raises(UnsupportedOperation):
            proxy_io.read()

    def test_readable(self, proxy_io):
        assert not proxy_io.readable()

    def test_readline(self, proxy_io):
        with pytest.raises(UnsupportedOperation):
            proxy_io.readline()

    def test_readlines(self, proxy_io):
        with pytest.raises(UnsupportedOperation):
            proxy_io.readlines()

    def test_seek(self, proxy_io):
        with pytest.raises(UnsupportedOperation):
            proxy_io.seek(0)

    def test_seekable(self, proxy_io):
        assert not proxy_io.seekable()

    def test_tell(self, proxy_io):
        assert proxy_io.tell() == 0

    def test_truncate(self, proxy_io):
        with pytest.raises(UnsupportedOperation):
            proxy_io.truncate()

    def test_writable(self, proxy_io):
        assert proxy_io.writable()

    def test_write(self, proxy_io, mock_stream):
        data = b"test data"
        result = proxy_io.write(data)
        assert result == len(data)
        assert proxy_io._pos == len(data)
        mock_stream.write.assert_called_once_with(data)

    def test_writelines(self, proxy_io, mock_stream):
        lines = [b"line1", b"line2"]
        proxy_io.writelines(lines)
        assert proxy_io._pos == sum(len(line) for line in lines)
        assert mock_stream.write.call_count == 2

    def test_next(self, proxy_io):
        with pytest.raises(UnsupportedOperation):
            next(proxy_io)

    def test_iter(self, proxy_io):
        assert iter(proxy_io) == proxy_io

    def test_exit(self, proxy_io):
        with proxy_io:
            pass
        assert proxy_io._closed

    def test_closed_operations(self, proxy_io):
        proxy_io.close()
        closed_ops = [
            lambda: proxy_io.flush(),
            lambda: proxy_io.isatty(),
            lambda: proxy_io.read(),
            lambda: proxy_io.readable(),
            lambda: proxy_io.readline(),
            lambda: proxy_io.readlines(),
            lambda: proxy_io.seek(0),
            lambda: proxy_io.seekable(),
            lambda: proxy_io.tell(),
            lambda: proxy_io.truncate(),
            lambda: proxy_io.writable(),
            lambda: proxy_io.write(b""),
            lambda: proxy_io.writelines([]),
            lambda: next(proxy_io),
            lambda: iter(proxy_io),
        ]
        for op in closed_ops:
            with pytest.raises(ValueError, match="I/O operation on closed file."):
                op()

    def test_with_bytesio(self, bytes_io):
        proxy = BinaryProxyIO(bytes_io)
        assert proxy.tell() == 0
        data = b"test data"
        proxy.write(data)
        assert bytes_io.getvalue() == data
        assert proxy.tell() == len(data)

    def test_with_file(self):
        with isolated_directory():
            filename = "test_file.bin"
            data = b"test data"
            with open(filename, 'wb') as f:
                proxy = BinaryProxyIO(f)
                assert proxy.tell() == 0
                proxy.write(data)
                assert proxy.tell() == len(data)

            with open(filename, 'rb') as f:
                assert f.read() == data

    def test_on_write(self):
        class CustomProxy(BinaryProxyIO):
            def __init__(self, stream):
                super().__init__(stream)
                self.on_write_called = False

            def _on_write(self, __s):
                self.on_write_called = True

        stream = BytesIO()
        proxy = CustomProxy(stream)
        proxy.write(b"test")
        assert proxy.on_write_called

    def test_after_close(self):
        class CustomProxy(BinaryProxyIO):
            def __init__(self, stream):
                super().__init__(stream)
                self.after_close_called = False

            def _after_close(self):
                self.after_close_called = True

        stream = BytesIO()
        proxy = CustomProxy(stream)
        proxy.close()
        assert proxy.after_close_called

    def test_with_bytesio_multi(self):
        initial_data = b"initial content"
        bytes_io = BytesIO(initial_data)
        bytes_io.seek(0, 2)  # Move to the end of initial content

        proxy = BinaryProxyIO(bytes_io)
        assert proxy.tell() == 0

        data_chunks = [b"chunk1", b"chunk2", b"chunk3"]
        expected_data = initial_data
        expected_tell = 0

        for chunk in data_chunks:
            proxy.write(chunk)
            expected_data += chunk
            expected_tell += len(chunk)
            assert bytes_io.getvalue() == expected_data
            assert proxy.tell() == expected_tell

        proxy.write(b"")  # Test empty write
        assert proxy.tell() == expected_tell

        proxy.writelines([b"line1", b"line2"])
        expected_data += b"line1line2"
        expected_tell += len(b"line1line2")
        assert bytes_io.getvalue() == expected_data
        assert proxy.tell() == expected_tell

        proxy.close()
        with pytest.raises(ValueError, match="I/O operation on closed file."):
            proxy.write(b"should not write")

        assert bytes_io.getvalue() == expected_data

    def test_with_file_multi(self):
        with isolated_directory():
            filename = "test_file.bin"
            initial_data = b"initial file content"

            # Write initial content
            with open(filename, 'wb') as f:
                f.write(initial_data)

            expected_data = initial_data
            expected_tell = 0

            with open(filename, 'r+b') as f:
                f.seek(0, 2)  # Move to the end of initial content
                proxy = BinaryProxyIO(f)
                assert proxy.tell() == 0

                data_chunks = [b"file_chunk1", b"file_chunk2", b"file_chunk3"]

                for chunk in data_chunks:
                    proxy.write(chunk)
                    expected_data += chunk
                    expected_tell += len(chunk)
                    assert proxy.tell() == expected_tell

                proxy.write(b"")  # Test empty write
                assert proxy.tell() == expected_tell

                proxy.writelines([b"file_line1", b"file_line2"])
                expected_data += b"file_line1file_line2"
                expected_tell += len(b"file_line1file_line2")
                assert proxy.tell() == expected_tell

                proxy.close()
                with pytest.raises(ValueError, match="I/O operation on closed file."):
                    proxy.write(b"should not write")

            # Verify file content after closing
            with open(filename, 'rb') as f:
                assert f.read() == expected_data

            # Test opening in write mode (should overwrite the file)
            new_data = b"completely new content"
            with open(filename, 'wb') as f:
                proxy = BinaryProxyIO(f)
                assert proxy.tell() == 0
                proxy.write(new_data)
                assert proxy.tell() == len(new_data)

            # Verify overwritten content
            with open(filename, 'rb') as f:
                assert f.read() == new_data

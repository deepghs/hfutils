import pytest

from hfutils.utils import splitext_with_composite


@pytest.mark.unittest
class TestSplitextWithComposite:
    @pytest.mark.parametrize("filename,composite_extensions,expected", [
        ("test.txt", [".txt"], ("test", ".txt")),
        ("test.pdf", [".pdf"], ("test", ".pdf")),
        ("test.doc", [".doc"], ("test", ".doc")),
        ("test.py", [".py"], ("test", ".py")),

        ("archive.tar.gz", [".tar.gz"], ("archive", ".tar.gz")),
        ("data.tar.bz2", [".tar.bz2"], ("data", ".tar.bz2")),
        ("video.tar.xz", [".tar.xz"], ("video", ".tar.xz")),
        ("backup.tar.7z", [".tar.7z"], ("backup", ".tar.7z")),

        ("test.tar.gz", [".tar.bz2", ".tar.gz"], ("test", ".tar.gz")),
        ("test.tar.bz2", [".tar.gz", ".tar.bz2"], ("test", ".tar.bz2")),

        ("TEST.TXT", [".txt"], ("TEST", ".TXT")),
        ("Test.PDF", [".pdf"], ("Test", ".PDF")),
        ("test.TAR.GZ", [".tar.gz"], ("test", ".TAR.GZ")),

        ("noextension", [], ("noextension", "")),
        ("noextension", [".txt"], ("noextension", "")),
        ("justname", [".tar.gz", ".txt"], ("justname", "")),

        (".hidden", [], (".hidden", "")),
        (".hidden.txt", [".txt"], (".hidden", ".txt")),
        (".config.json", [".json"], (".config", ".json")),

        ("my.test.file.txt", [".txt"], ("my.test.file", ".txt")),
        ("data.backup.tar.gz", [".tar.gz"], ("data.backup", ".tar.gz")),

        ("test-file.txt", [".txt"], ("test-file", ".txt")),
        ("test_file.tar.gz", [".tar.gz"], ("test_file", ".tar.gz")),
        ("test space.pdf", [".pdf"], ("test space", ".pdf")),

        ("test.txt", [], ("test", ".txt")),
        ("test.tar.gz", [], ("test.tar", ".gz")),

        ("test.xyz", [".txt", ".pdf", ".tar.gz"], ("test", ".xyz")),
        ("test.abc", [".def", ".ghi"], ("test", ".abc")),

        ("测试.txt", [".txt"], ("测试", ".txt")),
        ("тест.tar.gz", [".tar.gz"], ("тест", ".tar.gz")),

        (".", [], (".", "")),
        ("..", [], ("..", "")),
        ("..txt", [".txt"], (".", ".txt"))
    ])
    def test_splitext_with_composite(self, filename, composite_extensions, expected):
        result = splitext_with_composite(filename, composite_extensions)
        assert result == expected

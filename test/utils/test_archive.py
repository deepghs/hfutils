import os
from pathlib import Path

import pytest

from hfutils.utils.archive import is_archive_or_compressed


@pytest.mark.unittest
class TestUtilsArchive:
    @pytest.mark.parametrize("filename, expected", [
        ("file.tar", True),
        ("file.rar", True),
        ("file.zip", True),
        ("file.7z", True),
        ("file.gz", True),
        ("file.bz2", True),
        ("file.xz", True),
        ("file.ace", True),
        ("file.lz", True),
        ("file.lzma", True),
        ("file.z", True),
        ("file.cab", True),
        ("file.arj", True),
        ("file.iso", True),
        ("file.lzh", True),
        ("file.sit", True),
        ("file.sitx", True),
        ("file.sea", True),
        ("file.alz", True),
        ("file.egg", True),
        ("file.whl", True),
        ("file.deb", True),
        ("file.rpm", True),
        ("file.pkg", True),
        ("file.dmg", True),
        ("file.msi", True),
        ("file.tgz", True),
        ("file.tbz2", True),
        ("file.lzw", True),
        ("file.rz", True),
        ("file.lzo", True),
        ("file.zst", True),

        ("file.tar.gz", True),
        ("file.tar.bz2", True),
        ("file.tar.xz", True),
        ("file.tar.lz", True),
        ("file.tar.lzma", True),

        ("file.zipx", True),
        ("file.arc", True),
        ("file.ark", True),
        ("file.lha", True),
        ("file.zoo", True),
        ("file.gca", True),
        ("file.uc2", True),
        ("file.uha", True),
        ("file.war", True),
        ("file.ear", True),
        ("file.sar", True),
        ("file.jar", True),
        ("file.apk", True),
        ("file.xpi", True),
        ("file.snap", True),
        ("file.appimage", True),
        ("file.squashfs", True),
        ("file.cpio", True),
        ("file.shar", True),
        ("file.lbr", True),
        ("file.mar", True),
        ("file.sbx", True),
        ("file.qcow2", True),
        ("file.vdi", True),
        ("file.vhd", True),
        ("file.vmdk", True),
        ("file.ova", True),
        ("file.xar", True),
        ("file.mpq", True),

        ("file.tar.gz", True),
        ("file.t.lz", True),
        ("file.zipx", True),
        ("file.rar5", True),
        ("file.7zip", True),
        ("file.arj", True),
        ("file.lzma", True),
        ("file.gzip", True),
        ("file.bzip2", True),
        ("file.xz", True),
        ("file.lzh", True),
        ("file.iso", True),
        ("file.img", True),
        ("file.dmg", True),
        ("file.pkg", True),
        ("file.msi", True),
        ("file.deb", True),
        ("file.rpm", True),
        ("file.apk", True),
        ("file.ipa", True),

        ("文件.zip", True),
        ("ファイル.tar.gz", True),
        ("파일.rar", True),
        ("файл.7z", True),
        ("αρχείο.iso", True),
        ("फ़ाइल.deb", True),
        ("ملف.rpm", True),
        ("文件.exe", False),
        ("ファイル.txt", False),
        ("파일.doc", False),

        ("/home/user/file.zip", True),
        ("C:\\Users\\User\\file.rar", True),
        ("../relative/path/file.tar.gz", True),

        ("file.txt", False),
        ("file.exe", False),
        ("file.doc", False),
        ("file", False),
        ("", False),
    ])
    def test_is_archive_or_compressed(self, filename, expected):
        assert is_archive_or_compressed(filename) == expected

    @pytest.mark.parametrize("filename", [
        "FILE.ZIP", "File.Tar.Gz", "ARCHIVE.RAR", "package.DEB"
    ])
    def test_case_insensitive(self, filename):
        assert is_archive_or_compressed(filename)

    def test_no_extension(self, ):
        assert not is_archive_or_compressed("file_without_extension")

    def test_hidden_file(self, ):
        assert is_archive_or_compressed(".hidden_archive.zip")
        assert not is_archive_or_compressed(".hidden_file")

    def test_empty_filename(self, ):
        assert not is_archive_or_compressed("")

    def test_only_extension(self, ):
        assert is_archive_or_compressed(".zip")
        assert not is_archive_or_compressed(".txt")

    @pytest.mark.parametrize("filename, expected", [
        ("file.tar.gz", True),
        ("archive.tar.bz2", True),
        ("data.tar.xz", True),
        ("backup.tar.lz", True),
        ("compressed.tar.lzma", True),
        ("old_archive.tar.Z", True),
        ("legacy_file.tar.lzo", True),
        ("file.backup.tar.gz", True),
        ("archive.old.tar.bz2", True),
        ("文档.tar.gz", True),
        ("アーカイブ.tar.bz2", True),
        ("압축파일.tar.xz", True),
        ("архив.tar.lzma", True),
        ("αρχείο.tar.lz", True),
        ("File.TAR.GZ", True),
        ("ARCHIVE.Tar.Bz2", True),
        ("file.doc.pdf", False),
        ("archive.zip.txt", False),
        ("file.targz", False),
        ("archive.tarbz2", False),
        ("/home/user.name/file.tar.gz", True),
        ("C:\\Users\\user.name\\archive.tar.bz2", True),
        (".hidden_archive.tar.xz", True),
        (".tar.gz", True),
        (".tar.bz2", True),
    ])
    def test_compound_extensions(self, filename, expected):
        assert is_archive_or_compressed(filename) == expected

    def test_compound_extension_edge_cases(self):
        assert not is_archive_or_compressed("file.tar.")
        assert is_archive_or_compressed("file..tar.gz")
        assert is_archive_or_compressed(".tar.gz")
        assert is_archive_or_compressed("tar.gz")

    @pytest.mark.parametrize("filename", [
        "archive.tar", "data.tar.gz", "file.tar.bz2", "backup.tar.xz"
    ])
    def test_tar_pattern(self, filename):
        assert is_archive_or_compressed(filename)

    @pytest.mark.parametrize("filename", [
        "archive.t.gz", "data.t.bz", "file.t.xz", "backup.t.lz"
    ])
    def test_t_pattern(self, filename):
        assert is_archive_or_compressed(filename)

    @pytest.mark.parametrize("filename", [
        "archive.zip", "data.z"
    ])
    def test_zip_pattern(self, filename):
        assert is_archive_or_compressed(filename)

    def test_rar_pattern(self, ):
        assert is_archive_or_compressed("archive.rar")

    @pytest.mark.parametrize("filename", [
        "archive.r00", "data.r01", "file.r99"
    ])
    def test_r_pattern(self, filename):
        assert is_archive_or_compressed(filename)

    def test_7z_pattern(self, ):
        assert is_archive_or_compressed("archive.7z")

    @pytest.mark.parametrize("filename", [
        "archive.ar", "data.a"
    ])
    def test_ar_pattern(self, filename):
        assert is_archive_or_compressed(filename)

    @pytest.mark.parametrize("filename", [
        "archive.lz", "data.lzm", "file.lzma"
    ])
    def test_lz_pattern(self, filename):
        assert is_archive_or_compressed(filename)

    @pytest.mark.parametrize("filename", [
        "archive.gz", "data.gzip"
    ])
    def test_gz_pattern(self, filename):
        assert is_archive_or_compressed(filename)

    @pytest.mark.parametrize("filename", [
        "archive.bz", "data.bz2", "file.bzip", "backup.bzip2"
    ])
    def test_bz_pattern(self, filename):
        assert is_archive_or_compressed(filename)

    @pytest.mark.parametrize("filename", [
        "archive.xz", "data.lzh", "file.lha"
    ])
    def test_xz_lzh_pattern(self, filename):
        assert is_archive_or_compressed(filename)

    @pytest.mark.parametrize("filename", [
        "image.iso", "disk.img", "installer.dmg", "package.pkg", "setup.msi"
    ])
    def test_disk_image_pattern(self, filename):
        assert is_archive_or_compressed(filename)

    @pytest.mark.parametrize("filename", [
        "package.deb", "software.rpm", "app.apk", "application.ipa"
    ])
    def test_package_pattern(self, filename):
        assert is_archive_or_compressed(filename)

    # Test cases for non-matching filenames
    @pytest.mark.parametrize("filename", [
        "document.txt", "image.png", "script.py", "webpage.html",
        "archive.tar.txt", "file.zipper", "data.rarr", "backup.7zz",
        "program.exe", "library.dll", "sheet.xlsx", "presentation.pptx"
    ])
    def test_non_matching_patterns(self, filename):
        assert not is_archive_or_compressed(filename)

    # Test case sensitivity
    @pytest.mark.parametrize("filename", [
        "ARCHIVE.TAR", "DATA.ZIP", "FILE.RAR", "BACKUP.7Z",
        "Image.ISO", "Package.DEB", "Software.RPM", "App.APK"
    ])
    def test_case_insensitivity(self, filename):
        assert is_archive_or_compressed(filename)

    @pytest.mark.parametrize("filename, expected", [
        # Common archive formats
        ("file.tar", True),
        ("archive.zip", True),
        ("data.rar", True),
        ("backup.7z", True),

        # Compressed tar formats
        ("file.tar.gz", True),
        ("archive.tar.bz2", True),
        ("data.tar.xz", True),
        ("backup.tgz", True),
        ("file.tbz2", True),

        # Other compression formats
        ("document.gz", True),
        ("file.bz2", True),
        ("data.xz", True),
        ("archive.lz", True),
        ("file.lzma", True),
        ("data.Z", True),

        # Less common but valid formats
        ("file.cab", True),
        ("archive.iso", True),
        ("data.dmg", True),
        ("backup.vhd", True),

        # Split archives
        ("large_file.zip.001", True),
        ("big_archive.7z.001", True),
        ("huge_data.tar.gz.001", True),

        # Non-archive/compressed files
        ("document.txt", False),
        ("image.png", False),
        ("script.py", False),
        ("data.csv", False),

        # Edge cases
        ("archive.tar.gz.txt", False),  # Archive extension but .txt at the end
        (".htaccess", False),  # Hidden file, not an archive
        ("file_without_extension", False),
        ("archive.tar.123", True),  # Assuming this is considered valid
        ("data.001", False),  # Just a number extension, not necessarily an archive
    ])
    def test_is_archive_or_compressed(self, filename, expected):
        assert is_archive_or_compressed(filename) == expected

    # Test case insensitivity
    @pytest.mark.parametrize("filename", [
        "ARCHIVE.ZIP",
        "File.TaR.Gz",
        "DATA.RAR",
    ])
    def test_is_archive_or_compressed_case_insensitive(self, filename):
        assert is_archive_or_compressed(filename)

    # Test with path-like filenames
    @pytest.mark.parametrize("filename", [
        "/home/user/documents/archive.zip",
        "C:\\Users\\Documents\\backup.tar.gz",
        "../data/file.rar",
    ])
    def test_is_archive_or_compressed_with_paths(self, filename):
        assert is_archive_or_compressed(filename)

    # Test invalid inputs
    @pytest.mark.parametrize("invalid_input", [
        None,
        123,
        [],
        {},
    ])
    def test_is_archive_or_compressed_invalid_input(self, invalid_input):
        with pytest.raises(TypeError):  # Replace with specific exception if known
            is_archive_or_compressed(invalid_input)

    @pytest.mark.parametrize("filename, expected", [
        (Path("/home/user/file.zip"), True),
        (Path("/home/user/file.tar.gz"), True),
        (Path("/home/user/file.txt"), False),
        (Path("/home/user/file.7z"), True),
        (Path("/home/user/file.rar"), True),
        (Path("/home/user/file.iso"), True),
        (Path("/home/user/file.doc"), False),
        (Path("/home/user/file.zip.001"), True),
        (Path("/home/user/file.part1.rar"), True),
        (Path("/home/user/file.r00"), True),
        (Path("/home/user/file.001"), False),
    ])
    def test_is_archive_or_compressed_with_pathlib(self, filename, expected):
        assert is_archive_or_compressed(filename) == expected

    @pytest.mark.parametrize("filename, expected", [
        (os.path.join("home", "user", "file.zip"), True),
        (os.path.join("home", "user", "file.tar.gz"), True),
        (os.path.join("home", "user", "file.txt"), False),
        (os.path.join("home", "user", "file.7z"), True),
        (os.path.join("home", "user", "file.rar"), True),
        (os.path.join("home", "user", "file.iso"), True),
        (os.path.join("home", "user", "file.doc"), False),
        (os.path.join("home", "user", "file.zip.001"), True),
        (os.path.join("home", "user", "file.part1.rar"), True),
        (os.path.join("home", "user", "file.r00"), True),
        (os.path.join("home", "user", "file.001"), False),
    ])
    def test_is_archive_or_compressed_with_os_path(self, filename, expected):
        assert is_archive_or_compressed(filename) == expected

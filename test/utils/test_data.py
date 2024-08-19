import os

import pytest

from hfutils.utils import is_data_file


@pytest.mark.unittest
class TestUtilsData:
    @pytest.mark.parametrize("filename, expected", [
        ("data.json", True),
        ("file.csv", True),
        ("document.tsv", True),
        ("data.arrow", True),
        ("file.feather", True),
        ("data.parquet", True),
        ("file.avro", True),
        ("data.orc", True),
        ("array.npy", True),
        ("compressed.npz", True),
        ("data.hdf5", True),
        ("file.h5", True),
        ("matlab_data.mat", True),
        ("spss_file.sav", True),
        ("stata_data.dta", True),
        ("sas_data.sas7bdat", True),
        ("sas_transport.xpt", True),
        ("excel_file.xlsx", True),
        ("old_excel.xls", True),
        ("open_document.ods", True),
        ("database.db", True),
        ("sqlite_db.sqlite", True),
        ("access_db.mdb", True),
        ("new_access.accdb", True),
        ("dbase_file.dbf", True),
        ("feather_data.ftr", True),
        ("geo_data.geojson", True),
        ("shape_file.shp", True),
        ("keyhole_markup.kml", True),
        ("gps_data.gpx", True),
        ("netcdf_file.nc", True),
        ("gridded_data.grib", True),
        ("hierarchical_data.hdf", True),
        ("zarr_data.zarr", True),
        ("binary_data.bin", True),
        ("pickled_data.pickle", True),
        ("short_pickle.pkl", True),
        ("webassembly.wasm", True),
        ("text_file.txt", False),
        ("image.png", False),
        ("script.py", False),
        ("DATA.JSON", True),  # Test case insensitivity
        ("/path/to/data.csv", True),  # Test with path
        ("file_without_extension", False),
    ])
    def test_is_data_file(self, filename, expected):
        assert is_data_file(filename) == expected

    def test_is_data_file_with_pathlike(self):
        path = os.path.join("some", "path", "data.csv")
        assert is_data_file(os.fspath(path))

    def test_is_data_file_with_invalid_type(self):
        with pytest.raises(TypeError):
            is_data_file(123)

    def test_is_data_file_with_empty_string(self):
        assert not is_data_file("")

    @pytest.mark.parametrize("filename", [
        "file.json", "file.CSV", "FILE.JSON", "DATA.CSV",
        "/absolute/path/to/data.json",
        "relative/path/to/data.csv",
        r"C:\Windows\Path\To\data.tsv",
    ])
    def test_is_data_file_case_and_path_variations(self, filename):
        assert is_data_file(filename)

    @pytest.mark.parametrize("path", [
        "data/file.csv",
        "data\\file.csv",
        "/tmp/data.json",
        "C:\\Users\\User\\data.json",
        "~/documents/data.parquet",
        "..\\..\\data.arrow",
        "./data/file.feather",
    ])
    def test_is_data_file_different_path_styles(self, path):
        assert is_data_file(path)

    @pytest.mark.parametrize("filename", [
        "数据.csv",
        "données.json",
        "データ.parquet",
        "данные.arrow",
        "αρχείο.feather",
        "파일.npy",
        "ファイル.npz",
        "ملف.hdf5",
    ])
    def test_is_data_file_non_ascii_filenames(self, filename):
        assert is_data_file(filename)

    @pytest.mark.parametrize("path", [
        "/用户/数据/file.csv",
        "/utilisateur/données/file.json",
        "/ユーザー/データ/file.parquet",
        "/пользователь/данные/file.arrow",
        "/χρήστης/αρχείο/file.feather",
        "/사용자/파일/file.npy",
        "/ユーザー/ファイル/file.npz",
        "/المستخدم/ملف/file.hdf5",
    ])
    def test_is_data_file_non_ascii_paths(self, path):
        assert is_data_file(path)

    def test_is_data_file_windows_paths(self):
        assert is_data_file(r"C:\Users\用户\Documents\data.csv")
        assert is_data_file(r"\\server\share\データ.json")

    def test_is_data_file_macos_paths(self):
        assert is_data_file("/Users/ユーザー/Documents/data.parquet")
        assert is_data_file("/Volumes/External/données.arrow")

    def test_is_data_file_linux_paths(self):
        assert is_data_file("/home/пользователь/documents/data.feather")
        assert is_data_file("/mnt/external/αρχείο.npy")

    def test_is_data_file_with_os_path_objects(self):
        paths = [
            os.path.join("data", "file.csv"),
            os.path.join("用户", "数据", "file.json"),
            os.path.join("ユーザー", "データ", "file.parquet"),
        ]
        for path in paths:
            assert is_data_file(os.fspath(path))

    @pytest.mark.parametrize("path", [
        "file:///C:/Users/User/data.csv",
        "https://example.com/data.json",
        "ftp://ftp.example.com/data.parquet",
    ])
    def test_is_data_file_with_urls(self, path):
        assert is_data_file(path)

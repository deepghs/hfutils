"""
This module provides functionality for identifying data files based on their file extensions.

It includes a comprehensive set of data file extensions and a function to check if a given
filename corresponds to a known data file format. This can be useful in various data processing
and file handling scenarios where it's necessary to distinguish data files from other types of files.
"""

import os
from typing import Union

_DATA_EXTS = {
    '.json',  # JavaScript Object Notation
    '.csv',  # Comma-Separated Values
    '.tsv',  # Tab-Separated Values
    '.arrow',  # Apache Arrow file format
    '.feather',  # Feather file format (fast, language-agnostic columnar format)
    '.parquet',  # Apache Parquet file format
    '.avro',  # Apache Avro file format
    '.orc',  # Optimized Row Columnar file format
    '.npy',  # NumPy array file
    '.npz',  # NumPy compressed archive file
    '.hdf5',  # Hierarchical Data Format version 5
    '.h5',  # Alternative extension for HDF5
    '.mat',  # MATLAB file format
    '.sav',  # SPSS data file
    '.dta',  # Stata data file
    '.sas7bdat',  # SAS data file
    '.xpt',  # SAS transport file
    '.xlsx',  # Microsoft Excel Open XML Spreadsheet
    '.xls',  # Microsoft Excel Binary File Format
    '.ods',  # OpenDocument Spreadsheet
    '.db',  # Generic database file
    '.sqlite',  # SQLite database file
    '.mdb',  # Microsoft Access database file
    '.accdb',  # Microsoft Access database file (newer version)
    '.dbf',  # dBase database file
    '.ftr',  # Feather file format (alternative extension)
    '.geojson',  # GeoJSON file (for geographical data)
    '.shp',  # Shapefile (for geographical data)
    '.kml',  # Keyhole Markup Language (for geographical data)
    '.gpx',  # GPS Exchange Format
    '.nc',  # NetCDF (Network Common Data Form) file
    '.grib',  # GRIdded Binary or General Regularly-distributed Information in Binary form
    '.hdf',  # Hierarchical Data Format (older version)
    '.zarr',  # Zarr array storage format
    '.bin',  # Generic Binary File
    '.pickle',  # Pickle dumped file
    '.pkl',  # Shortcut of .pickle
    '.wasm',  # WASM
}


def is_data_file(filename: Union[str, os.PathLike]) -> bool:
    """
    Determine if a given filename corresponds to a known data file format.

    This function checks if the file extension of the provided filename matches
    any of the known data file extensions defined in the `_DATA_EXTS` set.

    :param filename: The name of the file to check. Can be a string or a path-like object.
    :type filename: Union[str, os.PathLike]

    :return: True if the file extension matches a known data file format, False otherwise.
    :rtype: bool

    :raises TypeError: If the provided filename is not a string or path-like object.

    Usage:
        >>> is_data_file('data.csv')
        True
        >>> is_data_file('script.py')
        False
        >>> is_data_file(Path('/path/to/data.json'))
        True

    .. note::
        The function is case-insensitive and works with both file names and full paths.
        It normalizes the filename and extracts only the extension for comparison.
    """
    if not isinstance(filename, (str, os.PathLike)):
        raise TypeError(f'Unknown file name type - {filename!r}')

    # Normalize the filename and get the extension
    filename = os.path.basename(os.path.normcase(str(filename)))
    _, ext = os.path.splitext(filename.lower())
    return ext in _DATA_EXTS

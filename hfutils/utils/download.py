import os
from typing import Optional

import requests

from .tqdm_ import tqdm


def download_file(url: str, filename: str, expected_size: Optional[int] = None, desc: Optional[str] = None,
                  session: Optional[requests.Session] = None, silent: bool = False, **kwargs) -> str:
    """
    Download a file from the given URL and save it to the specified filename.

    This function uses the requests library to download a file from the given URL
    and provides a progress bar using tqdm. It also performs checks to ensure that
    the downloaded file has the expected size.

    :param url: The URL of the file to download.
    :type url: str
    :param filename: The local path where the file should be saved.
    :type filename: str
    :param expected_size: The expected size of the file in bytes (optional).
    :type expected_size: int, optional
    :param desc: Description for the tqdm progress bar (optional).
    :type desc: str, optional
    :param session: An optional requests.Session object to use for the download.
    :type session: requests.Session, optional
    :param silent: If True, suppress tqdm output, otherwise display it.
    :type silent: bool
    :param kwargs: Additional keyword arguments to pass to requests.get().

    :return: The path to the downloaded file.
    :rtype: str
    """
    session = session or requests.session()
    response = session.get(url, stream=True, allow_redirects=True, **kwargs)
    expected_size = expected_size or response.headers.get('Content-Length', None)
    expected_size = int(expected_size) if expected_size is not None else expected_size

    desc = desc or os.path.basename(filename)
    directory = os.path.dirname(filename)
    if directory:
        os.makedirs(directory, exist_ok=True)

    with open(filename, 'wb') as f:
        with tqdm(total=expected_size, unit='B', unit_scale=True, unit_divisor=1024, desc=desc, silent=silent) as pbar:
            for chunk in response.iter_content(chunk_size=1024):
                f.write(chunk)
                pbar.update(len(chunk))

    actual_size = os.path.getsize(filename)
    if expected_size is not None and actual_size != expected_size:
        os.remove(filename)
        raise requests.exceptions.HTTPError(f"Downloaded file is not of expected size, "
                                            f"{expected_size} expected but {actual_size} found.")

    return filename

import os
from typing import Optional

import requests

from .tqdm_ import tqdm


def download_file(url, filename, expected_size: int = None, desc=None,
                  session: Optional[requests.Session] = None, silent: bool = False, **kwargs):
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

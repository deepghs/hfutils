from hashlib import sha256


def _f_sha256(file, chunk_for_hash: int = 1 << 20):
    """
    Calculate the SHA-256 hash of a file.

    :param file: The path to the file.
    :type file: str
    :param chunk_for_hash: The chunk size for hashing, defaults to 1 << 20 (1 MB).
    :type chunk_for_hash: int, optional
    :return: The SHA-256 hash of the file.
    :rtype: str
    """
    file_sha = sha256()
    with open(file, 'rb') as f:
        while True:
            data = f.read(chunk_for_hash)
            if not data:
                break
            file_sha.update(data)
    return file_sha.hexdigest()

from hashlib import sha256


def _f_sha256(file, chunk_for_hash: int = 1 << 20):
    file_sha = sha256()
    with open(file, 'rb') as f:
        while True:
            data = f.read(chunk_for_hash)
            if not data:
                break
            file_sha.update(data)
    return file_sha.hexdigest()

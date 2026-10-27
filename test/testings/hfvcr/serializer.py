"""
Cassette serializer: JSON with large bodies moved into a content-addressed blob store.

The default VCR.py YAML cassettes inline every body (``!!binary`` for non-text). That is unusable for
Hugging Face traffic, which is dominated by tar / parquet / image payloads. This serializer keeps the
interaction list in small, diff-friendly JSON and stores every body that is not short UTF-8 text as
``<blob_dir>/<sha256[:2]>/<sha256>.bin``. Identical payloads recorded by different tests are stored once.

The JSON is written with ``ensure_ascii=True`` so cassettes are pure ASCII: VCR.py reads and writes them
with the platform's default encoding, which is not UTF-8 on Windows.
"""
import hashlib
import json
import os
from typing import Any, Optional, Union

INLINE_LIMIT = 2048


class BlobJsonSerializer:
    """
    VCR.py serializer object (anything with ``serialize`` and ``deserialize`` works).

    :param blob_dir: Directory of the blob store.
    :param inline_limit: Text bodies up to this many bytes stay inline in the cassette.
    """

    def __init__(self, blob_dir: str, inline_limit: int = INLINE_LIMIT):
        self.blob_dir = blob_dir
        self.inline_limit = inline_limit

    def blob_path(self, sha: str) -> str:
        return os.path.join(self.blob_dir, sha[:2], f'{sha}.bin')

    @classmethod
    def _to_bytes(cls, body: Any) -> bytes:
        """A request body is whatever the client handed to the HTTP library: bytes, text, a list of chunks, a file."""
        if isinstance(body, (bytes, bytearray, memoryview)):
            return bytes(body)
        if isinstance(body, str):
            return body.encode('utf-8')
        if hasattr(body, 'read'):
            return cls._to_bytes(body.read())
        if isinstance(body, (list, tuple)):
            return b''.join(cls._to_bytes(item) for item in body)
        raise TypeError(f'Cannot store a request body of type {type(body).__name__}')

    def _encode(self, body: Union[None, str, bytes, list]) -> Optional[dict]:
        if body is None:
            return None
        data = self._to_bytes(body)
        if len(data) <= self.inline_limit:
            try:
                return {'text': data.decode('utf-8')}
            except UnicodeDecodeError:
                pass
        sha = hashlib.sha256(data).hexdigest()
        path = self.blob_path(sha)
        if not os.path.exists(path):
            os.makedirs(os.path.dirname(path), exist_ok=True)
            tmp = f'{path}.{os.getpid()}.tmp'
            with open(tmp, 'wb') as f:
                f.write(data)
            os.replace(tmp, path)
        return {'blob': sha, 'size': len(data)}

    def _decode(self, ref: Optional[dict]) -> Union[None, str, bytes]:
        if ref is None:
            return None
        if 'text' in ref:
            return ref['text']
        path = self.blob_path(ref['blob'])
        if not os.path.exists(path):
            raise FileNotFoundError(f'Blob {ref["blob"]} of a cassette is missing: {path}')
        with open(path, 'rb') as f:
            data = f.read()
        if len(data) != ref['size']:
            raise ValueError(f'Blob {ref["blob"]} is corrupted, size {len(data)} != {ref["size"]}')
        return data

    def serialize(self, cassette_dict: dict) -> str:
        interactions = []
        for item in cassette_dict['interactions']:
            request, response = dict(item['request']), dict(item['response'])
            request['body'] = self._encode(request.get('body'))
            response['body'] = self._encode((response.get('body') or {}).get('string'))
            interactions.append({'request': request, 'response': response})
        return json.dumps({'version': cassette_dict.get('version', 1), 'interactions': interactions},
                          indent=1, ensure_ascii=True, sort_keys=True) + '\n'

    def deserialize(self, cassette_string: str) -> dict:
        data = json.loads(cassette_string)
        for item in data['interactions']:
            item['request']['body'] = self._decode(item['request'].get('body'))
            item['response']['body'] = {'string': self._decode(item['response'].get('body'))}
        return data

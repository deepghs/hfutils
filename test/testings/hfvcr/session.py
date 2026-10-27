"""
The recording / replay session: cassette files, segments and recorded variables.

Terminology
-----------

``mode``
    ``none``    replay only; a request that is not in the cassette fails the test (this is also how the network is
                blocked: a test without a cassette has nothing to replay). The default, and what CI runs.
    ``new``     replay cassettes that exist, record the ones that do not.
    ``rewrite`` delete and record again every cassette the run touches.
    ``live``    no VCR at all, talk to the real endpoint (debugging / smoke checks).

*segment*
    One cassette file. A test owns a ``main`` segment that wraps the whole test, setup and teardown included.
    A fixture may open further segments (``HfVcrTest.segment``) so that its traffic lives in its own file.
    Segments nest; the innermost one answers.

*world*
    A segment shared by many tests, recorded once, replayed with repeats allowed. Meant for read-only reference
    data (``deepghs/game_character_skins`` and friends).

*variable*
    Something a fixture decides while recording and must decide the same way during replay, such as the random
    name of a temporary repository. It is stored next to the segment's cassette.
"""
import json
import os
import re
import hashlib
from contextlib import contextmanager
from typing import Callable, Any, Optional, Iterator

import vcr

from .scrub import FILTERED_REQUEST_HEADERS, match_query, match_path, scrub_response
from .replay import enable_safe_repeats, reset_http_sessions
from .serializer import BlobJsonSerializer

MODES = ('none', 'new', 'rewrite', 'live')

_SAFE = re.compile(r'[^A-Za-z0-9_.\-\[\]=,+]')


def safe_name(name: str, limit: int = 96) -> str:
    """File system safe, short, stable form of a test name or a segment name."""
    out = _SAFE.sub('_', name)
    if out != name or len(out) > limit:
        out = f'{out[:limit - 9]}-{hashlib.sha1(name.encode("utf-8")).hexdigest()[:8]}'
    return out


def variant_path(path: str, variant: str) -> str:
    """``a/b.json`` -> ``a/b@<variant>.json``"""
    return f'{os.path.splitext(path)[0]}@{variant}.json'


class Segment:
    """One active cassette file."""

    def __init__(self, path: str, recording: bool):
        self.path = path
        self.recording = recording
        self.vars_path = os.path.splitext(path)[0] + '.vars.json' if path else None
        self._vars = {}
        if not recording and self.vars_path and os.path.exists(self.vars_path):
            with open(self.vars_path, 'r') as f:
                self._vars = json.load(f)
        self._dirty = False

    def var(self, name: str, factory: Callable[[], Any]) -> Any:
        """
        A value decided while recording and replayed verbatim afterwards.

        :param name: Name of the variable, unique inside the segment.
        :param factory: Called only while recording (or live). Must return something JSON serializable.
        """
        if self.recording:
            value = factory()
            self._vars[name] = value
            self._dirty = True
            return value
        if name not in self._vars:
            raise KeyError(f'Variable {name!r} was never recorded in {self.vars_path!r}, '
                           f'record this test again with --hf-record=rewrite.')
        return self._vars[name]

    def _flush(self):
        if self.recording and self._dirty and self.vars_path:
            os.makedirs(os.path.dirname(self.vars_path), exist_ok=True)
            with open(self.vars_path, 'w') as f:
                json.dump(self._vars, f, indent=1, sort_keys=True, ensure_ascii=True)
                f.write('\n')


class HfVcr:
    """
    Owner of the VCR.py configuration of a test session.

    :param cassette_dir: Root directory of all cassettes (blobs live in ``<cassette_dir>/_blobs``).
    :param mode: One of :data:`MODES`.
    """

    def __init__(self, cassette_dir: str, mode: str = 'none', variant: Optional[str] = None,
                 record_variant: Optional[str] = None):
        if mode not in MODES:
            raise ValueError(f'Unknown mode {mode!r}, one of {MODES!r} expected.')
        self.cassette_dir = cassette_dir
        self.mode = mode
        #: Replay: a cassette ``<name>@<variant>.json``, when there is one, answers instead of ``<name>.json``.
        self.variant = variant
        #: Record: write ``<name>@<record_variant>.json`` instead of ``<name>.json``.
        self.record_variant = record_variant
        self.serializer = BlobJsonSerializer(os.path.join(cassette_dir, '_blobs'))
        #: Files written while recording, in order; a failed test discards its share (see :meth:`discard`).
        self.recorded = []
        self._vcr = vcr.VCR(
            serializer='hfjson',
            cassette_library_dir=cassette_dir,
            match_on=('method', 'scheme', 'host', 'port', 'hfpath', 'hfquery'),
            filter_headers=FILTERED_REQUEST_HEADERS,
            before_record_response=scrub_response,
            decode_compressed_response=True,
        )
        self._vcr.register_serializer('hfjson', self.serializer)
        self._vcr.register_matcher('hfquery', match_query)
        self._vcr.register_matcher('hfpath', match_path)

    @property
    def live(self) -> bool:
        return self.mode == 'live'

    def path_of(self, key: str) -> str:
        path = os.path.join(self.cassette_dir, *[safe_name(p) for p in key.split('/')]) + '.json'
        if self.record_variant:
            return variant_path(path, self.record_variant)
        if self.variant:
            candidate = variant_path(path, self.variant)
            if os.path.exists(candidate):
                return candidate
        return path

    def _record_mode(self, path: str) -> str:
        if self.mode == 'none':
            return 'none'
        if self.mode == 'new':
            return 'none' if os.path.exists(path) else 'once'
        # rewrite
        return 'once'

    @contextmanager
    def segment(self, key: str, repeats: bool = False) -> Iterator[Segment]:
        """
        Activate the cassette ``<cassette_dir>/<key>.json`` for the duration of the block.

        :param key: Slash separated name; each part is made file system safe.
        :param repeats: Allow a recorded response to be played more than once (read-only data only!).
        """
        if self.live:
            yield Segment(None, recording=True)  # no file: variables are simply decided anew
            return

        path = self.path_of(key)
        if self.mode == 'rewrite':
            for p in (path, os.path.splitext(path)[0] + '.vars.json'):
                if os.path.exists(p):
                    os.remove(p)
        record_mode = self._record_mode(path)
        segment = Segment(path, recording=(record_mode == 'once'))
        existed = os.path.exists(path)
        if segment.recording:
            self.recorded.append(path)
            self.recorded.append(segment.vars_path)
        try:
            reset_http_sessions()
            try:
                with self._vcr.use_cassette(path, record_mode=record_mode, allow_playback_repeats=repeats) as cassette:
                    enable_safe_repeats(cassette)
                    yield segment
            finally:
                reset_http_sessions()
        except BaseException:
            # never keep a half recorded cassette of a failed run
            if segment.recording and not existed and os.path.exists(path):
                os.remove(path)
            raise
        else:
            segment._flush()

    def discard(self, mark: int):
        """Delete everything recorded since ``len(self.recorded) == mark``: a failed test must leave nothing behind."""
        for path in self.recorded[mark:]:
            if os.path.exists(path):
                os.remove(path)
        del self.recorded[mark:]

    @contextmanager
    def guard(self) -> Iterator[None]:
        """
        Keep the real network out of everything that is not inside a segment, for the whole session: an empty cassette
        in ``none`` mode that nothing can be played from or recorded to. Every segment nests inside and overrides it.

        This holds while recording too: a module scoped fixture that talks to the service outside of any segment would
        otherwise work during recording (real network) and fail during replay, with nothing recorded.
        """
        if self.live:
            yield
            return
        with self._vcr.use_cassette(os.path.join(self.cassette_dir, '_guard_never_saved.json'), record_mode='none'):
            yield

    def world(self, name: str):
        """A segment shared between tests (read-only reference data), see the module documentation."""
        return self.segment(f'_worlds/{name}', repeats=True)


class HfVcrTest:
    """Per-test handle, the ``hf_vcr`` fixture."""

    def __init__(self, session: HfVcr, test_key: str):
        self.session = session
        self.test_key = test_key
        self.main: Optional[Segment] = None

    def segment(self, name: str, repeats: bool = False):
        """A fixture's own cassette of this test: ``<test>.<name>.json``."""
        return self.session.segment(f'{self.test_key}.{name}', repeats=repeats)

    def world(self, name: str):
        return self.session.world(name)

    @property
    def mode(self) -> str:
        return self.session.mode

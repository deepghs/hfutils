"""
Cassette framework for the unit tests: real Hugging Face traffic, recorded once, replayed everywhere.

See :mod:`.session` for the vocabulary and ``test/cassettes/README.md`` for how to record.
"""
from . import env  # noqa: F401  (first, see its docstring)
from .scrub import normalize_query, match_query, match_path, canonical_path
from .serializer import BlobJsonSerializer
from .session import HfVcr, HfVcrTest, Segment, MODES
from . import proxy

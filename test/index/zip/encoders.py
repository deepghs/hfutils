"""Encoders of the legacy zip methods, small and slow, written to mirror the decoders in ``hfutils.index.zip.legacy`` so that the tests
can feed them every path (growing code sizes, partial clears, follower sets, canonical Shannon-Fano tables). Real archives of
these methods are rare; what comes out of an encoder here is checked by decoding it and comparing it with the input."""
from collections import deque
from typing import Dict, List, Optional, Tuple


class BitWriter:
    """Little-endian bit packing, as every zip method uses."""

    def __init__(self):
        self.buf = bytearray()
        self.cur = 0
        self.nbits = 0

    def write(self, value: int, bits: int) -> None:
        self.cur |= (value & ((1 << bits) - 1)) << self.nbits
        self.nbits += bits
        while self.nbits >= 8:
            self.buf.append(self.cur & 0xff)
            self.cur >>= 8
            self.nbits -= 8

    def getvalue(self) -> bytes:
        return bytes(self.buf) + (bytes([self.cur & 0xff]) if self.nbits else b'')


# --- shrink -------------------------------------------------------------------------------------------------------------------

def shrink(data: bytes, partial_clears: bool = True, revived: Optional[list] = None) -> bytes:
    """LZW with 9-13 bit codes. Code size increases are announced with (256, 1); when the table is full a partial clear
    (256, 2) frees the codes that no other code builds on, like the decoder does. With ``partial_clears=False`` a full table is not
    cleared: the stream goes on without creating codes. ``revived`` collects the strings that a clear gave a new code."""
    out, size = BitWriter(), 9
    table: Dict[bytes, int] = {bytes([i]): i for i in range(256)}
    prefix_of: Dict[int, int] = {}
    string_of: Dict[int, bytes] = {}
    free = deque(range(257, 8192))
    pending: Optional[int] = None  # created by us, not yet by the decoder (it creates a code when it reads the next one)

    def emit(code: int) -> None:
        nonlocal size
        while code >= (1 << size) and size < 13:
            out.write(256, size)
            out.write(1, size)
            size += 1
        out.write(code, size)

    def partial_clear() -> None:
        # The decoder has not created our last code yet (it does when it reads the next one), so for the decoder that code is
        # free: the clear counts it among the codes to reuse, and the decoder then creates it again with the smallest free code.
        nonlocal pending
        entry = None
        if pending is not None:
            entry = (string_of[pending], prefix_of[pending])
            del table[entry[0]], prefix_of[pending], string_of[pending]
            free.append(pending)
        out.write(256, size)
        out.write(2, size)
        used = set(prefix_of.values())
        for code in sorted(c for c in prefix_of if c not in used):
            del table[string_of.pop(code)]
            del prefix_of[code]
            free.append(code)
        ordered = sorted(free)
        free.clear()
        free.extend(ordered)
        if entry is not None:
            pending = free.popleft()
            table[entry[0]], prefix_of[pending], string_of[pending] = pending, entry[1], entry[0]
            if revived is not None:
                revived.append(entry[0])

    w = b''
    i = 0
    while i < len(data):
        byte = data[i]
        wc = w + bytes([byte])
        if wc in table:
            w = wc
            i += 1
            continue
        if not free and partial_clears:
            partial_clear()
        if w not in table:
            # the clear freed the leaf that w is: send its prefix (which a longer entry builds on, so it is still there), make the
            # entry for w again, and look at the same byte once more
            cut = w[:-1]
            emit(table[cut])
            code = free.popleft()
            table[w], prefix_of[code], string_of[code] = code, table[cut], w
            pending = code
            w = w[-1:]
            continue
        emit(table[w])
        pending = None
        if free:
            code = free.popleft()
            table[wc], prefix_of[code], string_of[code] = code, table[w], wc
            pending = code
        w = bytes([byte])
        i += 1
    if w:
        emit(table[w])
    return out.getvalue()


# --- reduce -------------------------------------------------------------------------------------------------------------------

def _follower_bits(n: int) -> int:
    return 5 if n > 16 else 4 if n > 8 else 3 if n > 4 else 2 if n > 2 else 1 if n > 0 else 0


def reduce_stream(factor: int, followers: Dict[int, List[int]], tokens: List[Tuple]) -> bytes:
    """``tokens``: ``('lit', byte)`` or ``('run', length, distance)``. ``followers`` maps a byte to its (at most 32) followers."""
    out = BitWriter()
    for byte in range(255, -1, -1):
        fs = followers.get(byte, [])
        out.write(len(fs), 6)
        for f in fs:
            out.write(f, 8)
    prev = 0

    def byte_out(b: int) -> None:
        nonlocal prev
        fs = followers.get(prev, [])
        if not fs:
            out.write(b, 8)
        elif b in fs:
            out.write(0, 1)
            out.write(fs.index(b), _follower_bits(len(fs)))
        else:
            out.write(1, 1)
            out.write(b, 8)
        prev = b

    length_bits = 8 - factor
    max_base = (1 << length_bits) - 1
    for token in tokens:
        if token[0] == 'lit':
            byte_out(token[1])
            if token[1] == 144:
                byte_out(0)
            continue
        _, length, distance = token
        v, d = length - 3, distance - 1
        base = min(v, max_base)
        byte_out(144)
        byte_out(base | ((d >> 8) << length_bits))
        if base == max_base:
            byte_out(v - max_base)
        byte_out(d & 0xff)
    return out.getvalue()


def reduce_expected(tokens: List[Tuple]) -> bytes:
    out = bytearray()
    for token in tokens:
        if token[0] == 'lit':
            out.append(token[1])
        else:
            _, length, distance = token
            for _ in range(length):
                out.append(out[-distance] if distance <= len(out) else 0)
    return bytes(out)


# --- implode ------------------------------------------------------------------------------------------------------------------

def _uniform_table(count: int, length: int) -> bytes:
    """The code lengths of ``count`` symbols that all have ``length`` bits, run-length coded the way the stream wants them."""
    runs = []
    left = count
    while left:
        run = min(16, left)
        runs.append((length - 1) | ((run - 1) << 4))
        left -= run
    return bytes([len(runs) - 1]) + bytes(runs)


def implode(large_window: bool, literal_tree: bool, tokens: List[Tuple], min_len: int, tables: Optional[Dict[str, bytes]] = None
            ) -> bytes:
    """Every table is uniform (256 literals of 8 bits, 64 lengths and 64 distance symbols of 6 bits), so a symbol's code is its
    number, written inverted, most significant bit first. ``tables`` replaces the raw bytes of a table (to write broken ones)."""
    tables = tables or {}
    out = BitWriter()
    stream = BitWriter()  # the tables are whole bytes: write them in front
    head = b''
    if literal_tree:
        head += tables.get('literal', _uniform_table(256, 8))
    head += tables.get('length', _uniform_table(64, 6)) + tables.get('distance', _uniform_table(64, 6))
    for b in head:
        out.write(b, 8)

    def code(symbol: int, bits: int) -> None:
        for i in range(bits - 1, -1, -1):
            out.write(((symbol >> i) & 1) ^ 1, 1)

    distance_bits = 7 if large_window else 6
    for token in tokens:
        if token[0] == 'lit':
            out.write(1, 1)
            if literal_tree:
                code(token[1], 8)
            else:
                out.write(token[1], 8)
            continue
        _, length, distance = token
        d = distance - 1
        out.write(0, 1)
        out.write(d & ((1 << distance_bits) - 1), distance_bits)
        code(d >> distance_bits, 6)
        symbol = min(length - min_len, 63)
        code(symbol, 6)
        if symbol == 63:
            out.write(length - min_len - 63, 8)
    del stream
    return out.getvalue()

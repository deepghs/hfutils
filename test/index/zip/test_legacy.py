"""The legacy methods (shrink, reduce, implode): the real archives of zip-rs, then damaged copies of their streams, which must
only ever end in a :class:`ZipFormatError` (never an IndexError or an endless loop), and streams written by encoders in this file
for the paths that no real archive here takes."""
import random
import struct
import zlib

import pytest

from hfutils.index import ZipFormatError
from hfutils.index.zip.legacy import unshrink, expand, explode
from test.testings import get_testfile


def member(name):
    """``(flags, method, crc, size, stored bytes)`` of the first member of a fixture."""
    d = open(get_testfile('zipfiles', name), 'rb').read()
    _, _, flags, method, _, _, crc, csize, usize, nlen, elen = struct.unpack('<IHHHHHIIIHH', d[:30])
    start = 30 + nlen + elen
    return flags, method, crc, usize, d[start:start + csize]


def decode(method, flags, data, size, quirk=False):
    if method == 1:
        return unshrink(data, size)
    if 2 <= method <= 5:
        return expand(data, size, method - 1)
    return explode(data, size, bool(flags & 2), bool(flags & 4), quirk)


FIXTURES = ['thirdparty-ziprs-shrink.zip', 'thirdparty-ziprs-reduce.zip', 'thirdparty-ziprs-implode.zip']


@pytest.mark.unittest
class TestLegacyReal:
    @pytest.mark.parametrize('name', FIXTURES)
    def test_decodes_to_the_crc(self, name):
        flags, method, crc, size, data = member(name)
        assert zlib.crc32(decode(method, flags, data, size)) & 0xffffffff == crc

    @pytest.mark.parametrize('name', FIXTURES)
    def test_nothing_comes_out_of_nothing(self, name):
        flags, method, crc, size, data = member(name)
        if method == 1:  # an empty shrunk stream is an empty member: the reader's size check refuses it
            assert decode(method, flags, b'', size) == b''
        else:
            with pytest.raises(ZipFormatError):
                decode(method, flags, b'', size)

    @pytest.mark.parametrize('name', FIXTURES)
    def test_damaged_streams_end_in_a_format_error_or_in_bytes(self, name):
        flags, method, crc, size, data = member(name)
        rng = random.Random(name)
        outcomes = set()
        for i in range(600):
            mutated = bytearray(data)
            kind = i % 4
            if kind == 0:  # flip bits
                for _ in range(rng.randint(1, 4)):
                    mutated[rng.randrange(len(mutated))] ^= 1 << rng.randrange(8)
            elif kind == 1:  # cut
                del mutated[rng.randrange(1, len(mutated)):]
            elif kind == 2:  # overwrite a run with noise
                at = rng.randrange(len(mutated))
                mutated[at:at + 8] = bytes(rng.randrange(256) for _ in range(8))
            else:  # a wrong declared size
                pass
            declared = size if kind != 3 else rng.choice([0, 1, size // 2, size + 5, size * 3])
            try:
                out = decode(method, flags, bytes(mutated), declared)
                assert isinstance(out, bytes) and len(out) <= declared
                outcomes.add('bytes')
            except ZipFormatError:
                outcomes.add('error')
        assert outcomes == {'bytes', 'error'} or outcomes == {'error'}

    def test_implode_with_the_other_window_and_tree_flags_is_an_error_not_a_crash(self):
        flags, method, crc, size, data = member('thirdparty-ziprs-implode.zip')
        for f in (0, 2, 4, 6):
            for quirk in (False, True):
                try:
                    decode(method, f, data, size, quirk)
                except ZipFormatError:
                    pass


# ---------------------------------------------------------------------------------------------------------------------------------
# streams from the encoders in ``encoders.py``

import hashlib  # noqa: E402

from test.index.zip.encoders import shrink, reduce_stream, reduce_expected, implode  # noqa: E402


def noise(n, tag=b'x'):
    out = b''
    i = 0
    while len(out) < n:
        out += hashlib.sha256(tag + b'%d' % i).digest()
        i += 1
    return out[:n]


@pytest.mark.unittest
class TestShrinkEncoded:
    def test_text(self):
        data = b'to be or not to be, that is the question; ' * 40
        assert unshrink(shrink(data), len(data)) == data

    def test_code_sizes_grow(self):
        data = noise(3000) + noise(3000)[:1500] + noise(2000, b'y')
        assert unshrink(shrink(data), len(data)) == data

    def test_partial_clear_frees_and_reuses_codes(self):
        data = b''.join(noise(2000, b'%d' % i) + b'abcabcabcabcabcabc' * 4 for i in range(14))
        assert len(data) > 28000
        assert unshrink(shrink(data), len(data)) == data

    def test_a_code_made_right_at_a_partial_clear_can_be_used_later(self):
        # the clear frees the code that was just sent, so the decoder cannot know the length of the code made with it
        data = b''.join(noise(2000, b'%d' % i) + b'abcabcabcabcabcabc' * 4 for i in range(14))
        revived = []
        shrink(data, revived=revived)
        assert revived
        data += revived[0] + noise(300, b'tail') + revived[0]
        assert unshrink(shrink(data), len(data)) == data

    def test_a_full_table_without_a_clear_goes_on_without_new_codes(self):
        data = noise(24000)
        assert unshrink(shrink(data, partial_clears=False), len(data)) == data

    def test_a_repeat_after_a_clear_takes_the_prefix_of_a_freed_entry(self):
        data = noise(20000) * 2
        assert unshrink(shrink(data), len(data)) == data

    def test_the_new_code_after_a_clear_cannot_build_on_a_freed_one(self):
        from test.index.zip.encoders import BitWriter
        w = BitWriter()
        for code in (97, 98, 257, 256, 2, 257):  # a, b, ab, partial clear, then the next new code right away
            w.write(code, 9)
        with pytest.raises(ZipFormatError):
            unshrink(w.getvalue(), 100)

    def test_the_declared_size_is_enforced(self):
        data = noise(500)
        packed = shrink(data)
        with pytest.raises(ZipFormatError):
            unshrink(packed, len(data) - 100)
        assert unshrink(packed, len(data) + 100) == data  # a longer declared size only means the stream ends early

    def test_nothing_packs_to_nothing(self):
        assert shrink(b'') == b'' and unshrink(b'', 0) == b''


@pytest.mark.unittest
class TestReduceEncoded:
    FOLLOWERS = {ord('a'): [ord('b'), ord('c')], ord('b'): list(range(97, 110)), ord('z'): list(range(32)),
                 ord('y'): [1, 2, 3], 144: [0, 7], 0: [65], 65: [7, 9, 11, 13, 17, 19, 23, 29, 31]}

    @staticmethod
    def tokens(factor):
        max_base = (1 << (8 - factor)) - 1
        text = [('lit', c) for c in b'abacabadabacaba zzzy yz' * 30]
        return ([('lit', 65), ('run', 4, 200)]  # a distance beyond the start reads zeros
                + text + [('lit', 144), ('lit', 99), ('run', 4, 1), ('run', 10, 2), ('run', 3 + max_base + 7, 300),
                          ('run', 3 + max_base - 1, 400), ('run', 5, 500), ('lit', 144), ('lit', 144), ('lit', 5)])

    @pytest.mark.parametrize('factor', [1, 2, 3, 4])
    def test_round_trip(self, factor):
        tokens = self.tokens(factor)
        want = reduce_expected(tokens)
        assert expand(reduce_stream(factor, self.FOLLOWERS, tokens), len(want), factor) == want

    def test_without_follower_sets(self):
        tokens = [('lit', b) for b in b'plain text'] + [('run', 4, 5)]
        want = reduce_expected(tokens)
        assert expand(reduce_stream(2, {}, tokens), len(want), 2) == want

    @staticmethod
    def sets(first=None, zero=None):
        from test.index.zip.encoders import BitWriter
        w = BitWriter()
        for byte in range(255, -1, -1):
            n = first if (byte == 255 and first is not None) else (len(zero) if (byte == 0 and zero) else 0)
            w.write(n, 6)
            if byte == 0 and zero:
                for f in zero:
                    w.write(f, 8)
        return w

    def test_follower_set_too_big(self):
        with pytest.raises(ZipFormatError):
            expand(self.sets(first=33).getvalue() + bytes(100), 10, 1)

    def test_follower_index_out_of_range(self):
        w = self.sets(zero=[5])
        w.write(0, 1)  # not a literal ...
        w.write(1, 1)  # ... the second of one follower
        with pytest.raises(ZipFormatError):
            expand(w.getvalue() + bytes(4), 5, 1)

    def test_a_run_longer_than_what_is_left(self):
        tokens = [('lit', 65), ('lit', 66), ('run', 20, 1)]
        data = reduce_stream(1, {}, tokens)
        with pytest.raises(ZipFormatError):
            expand(data, 10, 1)

    def test_truncated(self):
        tokens = self.tokens(2)
        data = reduce_stream(2, self.FOLLOWERS, tokens)
        with pytest.raises(ZipFormatError):
            expand(data[:len(data) // 2], len(reduce_expected(tokens)), 2)


@pytest.mark.unittest
class TestImplodeEncoded:
    @staticmethod
    def tokens(min_len, distance_limit):
        text = [('lit', c) for c in b'hello implode world, hello implode world! ' * 4]
        return text + [('run', min_len, 1), ('run', 10, 5), ('run', min_len + 63 + 9, 3), ('run', min_len + 62, 20),
                       ('run', 4, distance_limit), ('lit', 0), ('lit', 255)]

    @pytest.mark.parametrize('large', [False, True])
    @pytest.mark.parametrize('literal', [False, True])
    def test_round_trip(self, large, literal):
        min_len = 3 if literal else 2
        tokens = self.tokens(min_len, 7000 if large else 3500)
        want = reduce_expected(tokens)
        assert explode(implode(large, literal, tokens, min_len), len(want), large, literal) == want

    @pytest.mark.parametrize('large', [False, True])
    @pytest.mark.parametrize('literal', [False, True])
    def test_the_pk101_rule_takes_the_other_minimum_length(self, large, literal):
        quirk_min = 3 if large else 2
        tokens = self.tokens(quirk_min, 3000)
        want = reduce_expected(tokens)
        assert explode(implode(large, literal, tokens, quirk_min), len(want), large, literal, True) == want

    def test_a_run_longer_than_what_is_left(self):
        tokens = [('lit', 65), ('run', 30, 1)]
        with pytest.raises(ZipFormatError):
            explode(implode(False, False, tokens, 2), 10, False, False)

    def test_truncated(self):
        tokens = self.tokens(2, 3000)
        data = implode(False, False, tokens, 2)
        with pytest.raises(ZipFormatError):
            explode(data[:len(data) - 12], len(reduce_expected(tokens)), False, False)

    @pytest.mark.parametrize('table', [
        bytes([0, 4 | (15 << 4)]),  # 16 symbols of 5 bits: fewer than the 64 that were announced
        bytes([4]) + bytes([5 | (15 << 4)]) * 5,  # 80 symbols for 64
        bytes([3]) + bytes([4 | (15 << 4)]) * 4,  # 64 symbols of 5 bits: more codes than there are bit strings
        bytes([3]) + bytes([6 | (15 << 4)]) * 4,  # 64 symbols of 7 bits: some bit strings are left over
    ])
    def test_broken_length_tables(self, table):
        with pytest.raises(ZipFormatError):
            explode(implode(False, False, [('lit', 65)], 2, {'length': table}), 1, False, False)

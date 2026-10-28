"""The corners of the zip reader: damaged and odd archives built by hand (see ``zipbuild``), the codecs and ciphers fed in small pieces,
and every error path. Together with the fixture tests they cover every line and every branch of ``hfutils/index/zip_*.py``."""
import lzma
import struct
import zipfile

import pytest

from hfutils.index.zip import codecs as zip_codecs, reader as zip_reader
from hfutils.index import zip_file_read, zip_list_files, ZipPasswordError, ZipPasswordRequiredError, \
    ZipUnsupportedError, ZipFormatError, ZipVolumeError, NotAZipError, ZipFetchError, zip_get_index, zip_cache_reset
from hfutils.index.zip.codecs import make_decompressor, _Object, _Lzma, _Whole
from hfutils.index.zip.crypto import zipcrypto_check_byte, ZipCryptoDecryptor, AesDecryptor, parse_aes_extra, aes_verifier_matches
from hfutils.index.zip.directory import build_directory, open_zip, find_eocd
from hfutils.index.zip.names import decode_name
from hfutils.index.zip.reader import ZipArchive
from hfutils.index.zip.source import BytesSource, FileSource, ConcatSource, ZipSource, HfSource
from test.index.zip.build import parts, eocd, zip_bytes, zip64_records, zip64_extra, zipcrypto_encrypt
from test.testings import get_testfile

HELLO = b'hello from the zip fixture\n'


def fx(name):
    return get_testfile('zipfiles', name)


def have(module):
    try:
        __import__(module)
        return True
    except ImportError:
        return False


def listing(data, **kwargs):
    return build_directory(BytesSource(data, 't.zip'), **kwargs)[0]


def archive(data, password=None):
    return ZipArchive(listing(data), password)


def opener(files):
    return lambda name: BytesSource(files[name], name) if name in files else None


@pytest.fixture(autouse=True)
def _fresh():
    zip_cache_reset()


@pytest.mark.unittest
class TestZipDirectoryCorners:
    def test_padding_after_the_comment_is_tolerated(self):
        data = zip_bytes([{'name': 'a.txt', 'data': b'x'}], comment=b'hi') + bytes(10)
        assert list(listing(data).files) == ['a.txt']
        assert find_eocd(data) is not None

    def test_a_signature_at_the_very_end_is_not_a_record(self):
        with pytest.raises(NotAZipError):
            listing(b'PK\x03\x04' + bytes(30) + b'PK\x05\x06' + bytes(5))

    def test_a_truncated_directory_record_ends_the_listing(self):
        body, cd = parts([{'name': 'a.txt', 'data': b'x'}, {'name': 'second-entry.txt', 'data': b'y'}])
        cut = cd[:-5]
        assert list(listing(body + cut + eocd(len(cut), len(body), 2)).files) == ['a.txt']

    @pytest.mark.parametrize('mask', range(16))
    def test_zip64_extra_fields_fill_exactly_the_saturated_ones(self, mask):
        size_s, csize_s, lho_s, disk_s = (bool(mask & b) for b in (1, 2, 4, 8))
        extra = zip64_extra(size=3 if size_s else None, csize=3 if csize_s else None, lho=0 if lho_s else None,
                            disk=0 if disk_s else None)
        entry = {'name': 'a.txt', 'data': b'abc', 'extra': extra}
        if size_s:
            entry['usize'] = 0xffffffff
        if csize_s:
            entry['csize'] = 0xffffffff
        if lho_s:
            entry['cd_lho'] = 0xffffffff
        if disk_s:
            entry['disk'] = 0xffff
        body, cd = parts([entry])
        e = listing(body + cd + eocd(len(cd), len(body), 1)).files['a.txt']
        assert (e.size, e.csize, e.offset, e.disk) == (3, 3, 0, 0)

    def test_a_saturated_field_without_its_zip64_value_stays_saturated(self):
        body, cd = parts([{'name': 'a.txt', 'data': b'abc', 'usize': 0xffffffff, 'extra': zip64_extra()}])
        assert listing(body + cd + eocd(len(cd), len(body), 1)).files['a.txt'].size == 0xffffffff

    def test_a_zip64_locator_that_points_to_nothing_is_noted(self):
        body, cd = parts([{'name': 'a.txt', 'data': b'x'}])
        locator = struct.pack('<4sIQI', b'PK\x06\x07', 0, 5, 1)
        d = listing(body + cd + locator + eocd(len(cd), len(body), 1))
        assert list(d.files) == ['a.txt'] and 'points to nothing' in d.notes[0]

    def test_zip64_records_are_used(self):
        body, cd = parts([{'name': 'a.txt', 'data': b'x'}])
        z64 = zip64_records(1, len(cd), len(body), len(body) + len(cd))
        d = listing(body + cd + z64 + eocd(0xffffffff, 0xffffffff, 1, comment=b''))
        assert list(d.files) == ['a.txt'] and d.notes == []

    def test_zip64_saturation_without_records(self):
        body, cd = parts([{'name': 'a.txt', 'data': b'x'}])
        with pytest.raises(ZipFormatError, match='ZIP64'):
            listing(body + cd + eocd(0xffffffff, len(body), 1))

    def test_a_directory_larger_than_the_file(self):
        with pytest.raises(ZipFormatError, match='truncated'):
            listing(bytes(30) + eocd(10 ** 6, 0, 1))

    def test_no_directory_where_the_end_record_says(self):
        with pytest.raises(ZipFormatError, match='no central directory'):
            listing(bytes(100) + eocd(40, 60, 1))

    def test_a_directory_beyond_the_tail_is_fetched_separately(self):
        names = [f'dir/with/a/rather/long/path/name-{i:05d}.txt' for i in range(3000)]
        body = zip_bytes([{'name': n, 'data': b''} for n in names])
        assert len(body) > 200_000  # more than what one tail read holds
        d = listing(body)
        assert len(d.files) == 3000 and d.tail_start > 0
        assert zip_list_files  # the public path reads the same


@pytest.mark.unittest
class TestZipVolumeCorners:
    def _disks(self, **override):
        body, cd = parts([{'name': 'a.txt', 'data': b'abc', **override}])
        last = cd + eocd(len(cd), 999_999, 1, this_disk=1, cd_disk=1)
        return body, last

    def test_a_directory_offset_outside_the_last_volume_is_found_in_front_of_the_end_record(self):
        body, last = self._disks()
        d = open_zip('x.zip', opener({'x.zip': last, 'x.z01': body}))
        assert list(d.files) == ['a.txt'] and d.volumes == ['x.z01', 'x.zip']
        assert zip_reader.ZipArchive(d).read('a.txt') == b'abc'

    def test_the_wrong_number_of_volumes(self):
        _, last = self._disks()
        with pytest.raises(ZipVolumeError, match='2 volumes'):
            build_directory(BytesSource(last), load_previous=lambda n: [])

    def test_an_entry_on_a_disk_that_does_not_exist(self):
        body, last = self._disks(disk=7)
        with pytest.raises(ZipFormatError, match='starts on disk 7'):
            open_zip('x.zip', opener({'x.zip': last, 'x.z01': body}))

    def test_a_missing_earlier_disk(self):
        _, last = self._disks()
        with pytest.raises(ZipVolumeError, match='x.z01'):
            open_zip('x.zip', opener({'x.zip': last}))

    def test_a_set_of_one_thousand_parts(self):
        files = {f'x.{n:03d}': bytes(10) for n in range(1, 1000)}
        with pytest.raises(ZipVolumeError, match='x.1000'):
            open_zip('x.001', opener(files))

    def test_raw_volumes_that_make_a_tar_say_so(self):
        import io
        import tarfile
        buf = io.BytesIO()
        with tarfile.open(fileobj=buf, mode='w') as tf:
            info = tarfile.TarInfo('a.txt')
            info.size = 1
            tf.addfile(info, io.BytesIO(b'a'))
        with pytest.raises(NotAZipError) as ei:
            open_zip('x.001', opener({'x.001': buf.getvalue()}))
        assert ei.value.detected == 'tar'

    def test_a_last_volume_alone_points_before_its_start(self):
        with pytest.raises(ZipVolumeError, match='x.001'):
            open_zip('x.003', opener({'x.003': open(fx('split-7z.zip.003'), 'rb').read()}))

    def test_offsets_before_the_start_of_a_plain_file(self):
        with pytest.raises(ZipFormatError, match='before the start'):
            listing(open(fx('split-7z.zip.003'), 'rb').read())

    def test_an_aes_member_needs_its_extra_field(self):
        body, cd = parts([{'name': 'a.txt', 'data': b'x', 'method': 99, 'flags': 1}])
        with pytest.raises(ZipFormatError, match='AES extra'):
            listing(body + cd + eocd(len(cd), len(body), 1))


@pytest.mark.unittest
class TestZipReaderCorners:
    def test_unlock_checks_aes_by_the_verifier(self):
        a = archive(open(fx('crypto-aes256.zip'), 'rb').read())
        assert not a.unlock('wrong') and a.passwords == []
        assert a.unlock('secret') and a.passwords == [b'secret']

    def test_unlock_checks_a_big_zipcrypto_member_by_its_header(self, monkeypatch):
        monkeypatch.setattr(zip_reader, '_FULL_CHECK_LIMIT', 0)
        a = archive(open(fx('crypto-zipcrypto.zip'), 'rb').read())
        assert not a.unlock('wrong')
        assert a.unlock('secret')

    def test_unlock_with_only_strong_members_has_nothing_to_check(self):
        a = ZipArchive(open_zip('s.zip', lambda n: FileSource(fx('thirdparty-libarchive-strong-encryption.zip'))))
        assert a.unlock('anything')

    def test_a_member_that_cannot_be_read_does_not_unlock(self):
        data = zip_bytes([{'name': 'a.txt', 'data': b'x', 'flags': 1, 'cd_lho': 5000}])
        assert not archive(data).unlock('secret')
        aes = zip_bytes([{'name': 'a.txt', 'data': b'x' * 40, 'flags': 1, 'method': 99, 'cd_lho': 5000,
                          'extra': struct.pack('<HHH2sBH', 0x9901, 7, 2, b'AE', 3, 0)}])
        assert not archive(aes).unlock('secret')

    def test_no_local_header(self):
        a = archive(zip_bytes([{'name': 'a.txt', 'data': b'x', 'cd_lho': 3}]))
        with pytest.raises(ZipFormatError, match='no local header'):
            a.read('a.txt')

    def test_the_archive_ends_in_the_middle_of_a_member(self):
        a = archive(zip_bytes([{'name': 'a.txt', 'data': b'x' * 10, 'csize': 10 ** 6, 'usize': 10 ** 6}]))
        with pytest.raises(ZipFormatError, match='truncated'):
            a.read('a.txt')

    def test_the_size_must_match(self):
        with pytest.raises(ZipFormatError, match='5 bytes came out, 7 expected'):
            archive(zip_bytes([{'name': 'a.txt', 'data': b'12345', 'usize': 7}])).read('a.txt')

    def test_the_crc_must_match(self):
        with pytest.raises(ZipFormatError, match='CRC'):
            archive(zip_bytes([{'name': 'a.txt', 'data': b'12345', 'crc': 1}])).read('a.txt')

    def test_a_limit_inside_a_whole_member_decoder(self):
        # the legacy methods give the member back at the very end: a limit cuts what they return
        assert len(zip_file_read(fx('thirdparty-ziprs-shrink.zip'), 'FIRST.TXT', limit=10)) == 10
        assert len(zip_file_read(fx('thirdparty-ziprs-shrink.zip'), 'FIRST.TXT', limit=10_000)) == 1092

    def test_strong_encryption_flag_alone_is_encryption(self):
        a = archive(zip_bytes([{'name': 'a.txt', 'data': b'x', 'flags': 0x40}]))
        with pytest.raises(ZipUnsupportedError, match='strong'):
            a.read('a.txt', password='x')
        with pytest.raises(ZipUnsupportedError, match='strong'):
            list(a.iter_chunks('a.txt', password='x'))

    def test_iter_chunks(self):
        a = ZipArchive(open_zip('m.zip', lambda n: FileSource(fx('crypto-zipcrypto.zip'))))
        assert b''.join(a.iter_chunks('hello.txt', password='secret')) == HELLO
        assert a.passwords == [b'secret']
        assert b''.join(a.iter_chunks('hello.txt')) == HELLO  # remembered
        with pytest.raises(ZipPasswordError, match='wrong password'):
            list(archive(open(fx('crypto-zipcrypto.zip'), 'rb').read()).iter_chunks('hello.txt', password='nope'))
        with pytest.raises(ZipPasswordRequiredError):
            list(archive(open(fx('crypto-zipcrypto.zip'), 'rb').read()).iter_chunks('hello.txt'))
        plain = archive(open(fx('methods-bzip2.zip'), 'rb').read())
        assert b''.join(plain.iter_chunks('hello.txt')) == HELLO

    def test_an_empty_encrypted_member(self):
        data = zip_bytes([{'name': 'e.txt', 'data': zipcrypto_encrypt(b'pw', b'', 0), 'flags': 1, 'usize': 0, 'crc': 0}])
        a = archive(data)
        assert list(a.iter_chunks('e.txt', password='pw')) == [] and a.passwords == [b'pw']
        assert archive(data).read('e.txt', password='pw') == b''

    def test_a_wrong_password_that_passes_the_check_byte_is_caught_by_the_crc(self):
        # find a wrong password whose header check byte matches by luck (one in 256), then the CRC must refuse it
        plain = b'some content that is long enough to be wrong with another key'
        import zlib
        crc = zlib.crc32(plain) & 0xffffffff
        data = zip_bytes([{'name': 'a.txt', 'data': zipcrypto_encrypt(b'right', plain, crc >> 24), 'flags': 1, 'crc': crc,
                           'usize': len(plain)}])
        lucky = next(pw for pw in (f'guess{i}'.encode() for i in range(100_000))
                     if ZipCryptoDecryptor.header_matches(pw, zipcrypto_encrypt(b'right', plain, crc >> 24)[:12], crc >> 24))
        a = archive(data)
        with pytest.raises(ZipPasswordError, match='CRC'):
            a.read('a.txt', password=lucky.decode())
        assert a.read('a.txt', password=[lucky.decode(), 'right']) == plain  # the next candidate is tried
        with pytest.raises(ZipPasswordError, match='CRC'):
            list(archive(data).iter_chunks('a.txt', password=lucky.decode()))  # a streaming caller gets the error

    def test_unsupported_method_comes_before_the_password(self):
        a = archive(zip_bytes([{'name': 'a.txt', 'data': b'x', 'method': 98, 'flags': 1}]))
        with pytest.raises(ZipUnsupportedError, match='98'):
            a.read('a.txt')
        with pytest.raises(ZipUnsupportedError, match='98'):
            list(a.iter_chunks('a.txt'))


@pytest.mark.unittest
class TestZipCodecCorners:
    def test_a_damaged_deflate_stream(self):
        with pytest.raises(ZipFormatError, match='deflate'):
            make_decompressor(8, 0, 10).feed(b'\xff\xff\xff\xff\xff\xff')

    def test_a_flush_that_fails(self):
        class Bad:
            def decompress(self, chunk):
                return b''

            def flush(self):
                raise ValueError('boom')

        with pytest.raises(ZipFormatError, match='boom'):
            _Object(Bad(), 'x').finish()

    @staticmethod
    def _lzma(data, dict_size=1 << 16, lc=3, lp=0, pb=2):
        raw = lzma.compress(data, format=lzma.FORMAT_RAW, filters=[
            {'id': lzma.FILTER_LZMA1, 'dict_size': dict_size, 'lc': lc, 'lp': lp, 'pb': pb}])
        return b'\x09\x14\x05\x00' + bytes([(pb * 5 + lp) * 9 + lc]) + struct.pack('<I', dict_size) + raw

    def test_lzma_fed_one_byte_at_a_time(self):
        stream, data = self._lzma(b'abcdef' * 100), b'abcdef' * 100
        d = _Lzma(0, len(data))
        out = b''.join(d.feed(stream[i:i + 1]) for i in range(len(stream))) + d.finish()
        assert out == data

    def test_lzma_output_is_cut_at_the_declared_size(self):
        d = _Lzma(0, 3)
        assert d.feed(self._lzma(b'abcdef')) == b'abc'

    def test_lzma_data_after_the_end(self):
        stream = self._lzma(b'abcdef')
        d = _Lzma(0, 6)
        d.feed(stream)
        if d.obj.eof:
            assert d.feed(b'more') == b''
        else:  # a raw stream without an end marker is ended by the size only
            assert d.feed(b'') == b''

    def test_lzma_header_errors(self):
        with pytest.raises(ZipFormatError, match='4 bytes'):
            _Lzma(0, 1).feed(b'\x09\x14\x04\x00' + bytes(4))
        with pytest.raises(ZipFormatError, match='properties are invalid'):
            _Lzma(0, 1).feed(b'\x09\x14\x05\x00' + bytes([225]) + bytes(4))
        with pytest.raises(ZipFormatError, match='damaged'):
            _Lzma(0, 100).feed(self._lzma(b'abcdef' * 10)[:12] + b'\xff' * 30)

    def test_implode_is_read_again_with_the_pk101_rule(self, monkeypatch):
        calls = []

        def fake(data, size, large, literal, quirk=False):
            calls.append(quirk)
            if not quirk:
                raise ZipFormatError('first rule fails')
            return b'ok'

        monkeypatch.setattr(zip_codecs, 'explode', fake)
        w = _Whole(6, 6, 2)
        w.feed(b'xx')
        assert w.finish() == b'ok' and calls == [False, True]

    def test_zstd_is_never_a_silent_failure(self):
        if have('compression.zstd') or have('zstandard'):
            assert make_decompressor(93, 0, 1) is not None
        else:
            with pytest.raises(ZipUnsupportedError):
                make_decompressor(93, 0, 1)


@pytest.mark.unittest
class TestZipCryptoCorners:
    @staticmethod
    def _member(name):
        d = open_zip(name, lambda n: FileSource(fx(name)))
        a = ZipArchive(d)
        e = d.files['hello.txt']
        start = a._data_start(e)
        return e, a.source.fetch(start, e.csize)

    def test_zipcrypto_header_across_chunks(self):
        e, raw = self._member('crypto-zipcrypto.zip')
        check = zipcrypto_check_byte(e.crc, e.dos_time, bool(e.flags & 8))
        dec = ZipCryptoDecryptor(b'secret', check)
        out = b''.join(dec.feed(raw[i:i + 5]) for i in range(0, len(raw), 5)) + dec.finish()
        assert out == HELLO
        assert ZipCryptoDecryptor.header_matches(b'secret', raw[:12], check)
        assert not ZipCryptoDecryptor.header_matches(b'nope', raw[:12], check)  # fixed bytes: this one is refused

    def test_a_member_shorter_than_its_header(self):
        dec = ZipCryptoDecryptor(b'secret', 0)
        assert dec.feed(b'12345') == b''
        with pytest.raises(ZipFormatError, match='12-byte header'):
            dec.finish()

    def test_aes_extra_field_parsing(self):
        assert parse_aes_extra(b'') is None
        other = struct.pack('<HH', 0x5455, 5) + bytes(5)
        aes = struct.pack('<HHH2sBH', 0x9901, 7, 2, b'AE', 3, 8)
        assert parse_aes_extra(other + aes) == (2, 256, 8)
        with pytest.raises(ZipUnsupportedError, match='strength'):
            parse_aes_extra(struct.pack('<HHH2sBH', 0x9901, 7, 2, b'AE', 9, 8))

    def test_the_aes_verifier_without_the_cipher(self):
        d = open_zip('a.zip', lambda n: FileSource(fx('crypto-aes256.zip')))
        e = d.files['hello.txt']
        head = ZipArchive(d)._raw(e, 0, 18)
        assert aes_verifier_matches(b'secret', 256, head) and not aes_verifier_matches(b'other', 256, head)

    def test_aes_in_small_pieces_and_cut_short(self):
        pytest.importorskip('cryptography')
        d = open_zip('a.zip', lambda n: FileSource(fx('crypto-aes256.zip')))
        e, a = d.files['hello.txt'], ZipArchive(d)
        raw = a.source.fetch(a._data_start(e), e.csize)
        dec = AesDecryptor(b'secret', 256)
        out = b''.join(dec.feed(raw[i:i + 1]) for i in range(len(raw))) + dec.finish()
        assert out == HELLO
        with pytest.raises(ZipFormatError, match='shorter'):
            AesDecryptor(b'secret', 256).finish()
        short = AesDecryptor(b'secret', 256)
        short.feed(raw[:20])  # the header and a few bytes: less than the 10-byte tag after the header
        with pytest.raises(ZipFormatError, match='shorter'):
            short.finish()
        with pytest.raises(ZipPasswordError):
            AesDecryptor(b'wrong', 256).feed(raw)


@pytest.mark.unittest
class TestZipSourceAndNames:
    def test_sources(self):
        s = BytesSource(b'0123456789')
        assert s.fetch(2, 3) == b'234' and s.fetch_range(8, 100) == b'89' and s.fetch_range(20, 5) == b''
        with pytest.raises(NotImplementedError):
            ZipSource().fetch(0, 1)
        c = ConcatSource([BytesSource(b'abc'), BytesSource(b'def')])
        assert c.size == 6 and c.fetch(2, 3) == b'cde'

    def _hf(self, monkeypatch, behaviour):
        import hfutils.index.zip.source as zs
        monkeypatch.setattr(zs, 'http_get', behaviour)
        return HfSource('o/r', 'a.zip', 100)

    def test_a_failed_request_keeps_its_status(self, monkeypatch):
        class Err(Exception):
            response = type('R', (), {'status_code': 503})()

        def boom(*a, **k):
            raise Err('down')

        with pytest.raises(ZipFetchError) as ei:
            self._hf(monkeypatch, boom).fetch(0, 10)
        assert ei.value.status == 503 and 'a.zip' in str(ei.value)

        def plain(*a, **k):
            raise OSError('reset')

        with pytest.raises(ZipFetchError) as ei:
            self._hf(monkeypatch, plain).fetch(0, 10)
        assert ei.value.status is None

    def test_a_short_answer_is_an_error(self, monkeypatch):
        def short(url, buf, **k):
            buf.write(b'12345')

        with pytest.raises(ZipFetchError, match='got 5'):
            self._hf(monkeypatch, short).fetch(0, 10)

    def test_utf8_flagged_names(self):
        import io
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, 'w') as zf:
            zf.writestr('日本語/ファイル.txt', b'x')
        import os
        from hbutils.testing import isolated_directory
        with isolated_directory():
            with open('u.zip', 'wb') as f:
                f.write(buf.getvalue())
            assert zip_list_files('u.zip') == ['日本語/ファイル.txt']
            assert zip_get_index('u.zip')['encoding'] == 'utf-8' and os.path.exists('u.zip')
        assert decode_name('é'.encode('utf-8'), 0x800, None, 'cp437') == 'é'

    def test_no_cache_always_reads_again(self):
        zip_get_index(fx('methods-bzip2.zip'), no_cache=True)
        assert zip_get_index(fx('methods-bzip2.zip'), no_cache=True)['files']

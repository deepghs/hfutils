# Zip fixtures

Small archives for `test/utils/test_zip_archive.test.js` and the zip-mode
`TarBrowserPanel` tests. Archives the tests can build themselves (stored and
deflated members, AES and ZipCrypto written by zip.js) are generated in the
tests instead of being checked in.

`make-fixtures.sh` regenerates every non-`thirdparty-*` file. It needs Python
3.14 (stdlib `zstd`) with Pillow, Info-ZIP `zip` and 7-Zip. The content is a
short text file, a nested markdown file, a CSV and a 96 px noise JPEG; split
sets also carry 180 KB of random bytes so that they span several volumes.

| File | What it covers |
| --- | --- |
| `methods-bzip2.zip`, `methods-lzma.zip`, `methods-zstd.zip` | Python `zipfile` methods 12, 14 (EOS marker) and 93 |
| `methods-lzma-7z.zip`, `methods-deflate64.zip`, `methods-ppmd.zip` | 7-Zip LZMA, Deflate64 (9) and PPMd (98, unsupported) |
| `crypto-aes256.zip`, `crypto-aes256-bzip2.zip` | WinZip AES-256, alone and over bzip2; password `secret` |
| `crypto-zipcrypto.zip`, `crypto-zipcrypto-stream.zip` | ZipCrypto with and without data descriptors; password `secret` |
| `crypto-two-passwords.zip` | Entries encrypted with `alpha` and with `beta` |
| `crypto-partial.zip` | One plain entry and one ZipCrypto entry (`secret`) |
| `split-infozip.z01` … `split-infozip.zip` | Info-ZIP disk set, offsets relative to each disk |
| `split-7z.zip.001` … `.003` | 7-Zip volumes: a byte split of one ordinary zip |
| `prefix-sfx.zip` | 4 KB of data before the archive, offsets not adjusted |
| `zip64-missing-records.zip` | Info-ZIP `-fz` to a pipe: EOCD offset `0xFFFFFFFF` without ZIP64 records |
| `names-shiftjis.zip`, `names-gbk.zip`, `names-cp866.zip` | Legacy codepage names without the UTF-8 flag |
| `names-odd.zip` | `../`, absolute, dotted and duplicate names, a directory entry, an empty file |
| `empty.zip` | No entries |

Third-party samples, copied unchanged:

| File | Source | License |
| --- | --- | --- |
| `thirdparty-libarchive-xz.zipx` | libarchive `test_read_format_zip_xz_multi.zipx` | BSD-2-Clause |
| `thirdparty-libarchive-lzma-sized.zipx` | libarchive `test_read_format_zip_lzma.zipx` (LZMA without EOS marker) | BSD-2-Clause |
| `thirdparty-libarchive-encrypted-directory.zip` | libarchive `test_read_format_zip_encryption_header.zip` | BSD-2-Clause |
| `thirdparty-libarchive-strong-encryption.zip` | libarchive `test_read_format_zip_encryption_data.zip` | BSD-2-Clause |
| `thirdparty-libarchive-unicode-path.zip` | libarchive `test_read_format_zip_7075_utf8_paths.zip` (Info-ZIP Unicode Path extra field) | BSD-2-Clause |
| `thirdparty-ziprs-implode.zip`, `-shrink.zip`, `-reduce.zip` | zip-rs `tests/data/legacy/` | MIT |

libarchive: https://github.com/libarchive/libarchive (libarchive/test).
zip-rs: https://github.com/zip-rs/zip2 (tests/data).

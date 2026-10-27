#!/usr/bin/env bash
# Regenerates the zip fixtures used by test/utils/test_zip_archive.test.js.
# Needs Python 3.14 (stdlib zstd), Pillow, Info-ZIP zip and 7-Zip on PATH.
# Third-party samples (see README.md) are copied, not regenerated.
set -euo pipefail
cd "$(dirname "$0")"
PY="${PY:-python3.14}"
W="$(mktemp -d)"; trap 'rm -rf "$W"' EXIT
"$PY" - "$W" <<'PYEOF'
import io, os, random, sys
from pathlib import Path
from PIL import Image
root = Path(sys.argv[1]) / "src"; random.seed(20261005)
def w(p, data):
    p = root / p; p.parent.mkdir(parents=True, exist_ok=True); p.write_bytes(data if isinstance(data, bytes) else data.encode())
w("hello.txt", "hello from the zip fixture\n")
w("docs/readme.md", "# Fixture\n\nNested markdown member.\n")
w("data/table.csv", "id,name\n" + "".join(f"{i},row-{i}\n" for i in range(200)))
# Noise JPEG: the bzip2 decoder that shipped in an earlier prototype corrupted exactly this kind of member.
img = Image.frombytes("RGB", (96, 96), bytes(random.getrandbits(8) for _ in range(96 * 96 * 3)))
buf = io.BytesIO(); img.save(buf, "JPEG", quality=90); w("images/noise.jpg", buf.getvalue())
PYEOF
S="$W/src"
pyzip() { (cd "$S" && "$PY" - "$@" <<'PYEOF'
import sys, zipfile, os
out, method = sys.argv[1], getattr(zipfile, sys.argv[2])
with zipfile.ZipFile(out, "w", method) as z:
    for dp, _, fn in sorted(os.walk(".")):
        for f in sorted(fn): z.write(os.path.join(dp, f), os.path.relpath(os.path.join(dp, f), "."))
PYEOF
) }
pyzip "$PWD/methods-bzip2.zip" ZIP_BZIP2
pyzip "$PWD/methods-lzma.zip" ZIP_LZMA
pyzip "$PWD/methods-zstd.zip" ZIP_ZSTANDARD
rm -f ./*.zip.0* ./*.z0* methods-deflate64.zip methods-ppmd.zip methods-lzma-7z.zip crypto-*.zip split-*.zip prefix-sfx.zip zip64-missing-records.zip
(cd "$S" && 7z a -bd -tzip -mm=Deflate64 "$OLDPWD/methods-deflate64.zip" . >/dev/null)
(cd "$S" && 7z a -bd -tzip -mm=PPMd "$OLDPWD/methods-ppmd.zip" data >/dev/null)
(cd "$S" && 7z a -bd -tzip -mm=LZMA "$OLDPWD/methods-lzma-7z.zip" data >/dev/null)
(cd "$S" && 7z a -bd -tzip -psecret -mem=AES256 "$OLDPWD/crypto-aes256.zip" . >/dev/null)
(cd "$S" && 7z a -bd -tzip -psecret -mem=AES256 -mm=BZip2 "$OLDPWD/crypto-aes256-bzip2.zip" hello.txt images >/dev/null)
(cd "$S" && zip -q -r -P secret "$OLDPWD/crypto-zipcrypto.zip" .)
(cd "$S" && zip -q -r -P secret - . | cat > "$OLDPWD/crypto-zipcrypto-stream.zip")
(cd "$S" && zip -q -r -P alpha "$OLDPWD/crypto-two-passwords.zip" hello.txt docs && zip -q -r -P beta "$OLDPWD/crypto-two-passwords.zip" data)
(cd "$S" && zip -q -r "$OLDPWD/crypto-partial.zip" hello.txt && zip -q -r -P secret "$OLDPWD/crypto-partial.zip" docs)
head -c 180000 /dev/urandom > "$S/blob.bin"
(cd "$S" && zip -q -r -s 64k "$OLDPWD/split-infozip.zip" .)
(cd "$S" && 7z a -bd -tzip -v64k "$OLDPWD/split-7z.zip" . >/dev/null)
rm "$S/blob.bin"
(cd "$S" && zip -q -r -fz - hello.txt docs | cat > "$OLDPWD/zip64-missing-records.zip")
{ head -c 4096 /dev/urandom; (cd "$S" && zip -q -r - hello.txt docs | cat); } > prefix-sfx.zip
"$PY" - <<'PYEOF'
import zipfile, warnings
def legacy(name, names, enc):
    raw = [n.encode(enc) for n in names]; ph = [chr(65 + i).encode() * len(r) for i, r in enumerate(raw)]
    with zipfile.ZipFile(name, "w", zipfile.ZIP_DEFLATED) as z:
        for p, n in zip(ph, names): z.writestr(p.decode(), f"{n}\n".encode())
    data = open(name, "rb").read()
    for p, r in zip(ph, raw): assert data.count(p) == 2; data = data.replace(p, r)
    open(name, "wb").write(data)
legacy("names-shiftjis.zip", ["画像/猫.txt", "テスト資料.txt"], "shift_jis")
legacy("names-gbk.zip", ["图片/猫猫.txt", "测试资料.txt"], "gbk")
legacy("names-cp866.zip", ["Привет/мир.txt"], "cp866")
warnings.simplefilter("ignore")
with zipfile.ZipFile("names-odd.zip", "w") as z:
    z.writestr("../escape.txt", "traversal\n"); z.writestr("/abs/path.txt", "absolute\n")
    z.writestr("a/./b/../c.txt", "dots\n"); z.writestr("dup.txt", "first\n"); z.writestr("dup.txt", "second\n")
    z.writestr("only/dir/", ""); z.writestr("empty.txt", "")
with zipfile.ZipFile("empty.zip", "w"): pass
PYEOF
ls -la

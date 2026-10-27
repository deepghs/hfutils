# Cassettes

Every test of `hfutils` runs against **recorded Hugging Face traffic**. The first run against the real
service wrote these files; every later run (CI included) replays them, with the network blocked.
`huggingface_hub` and `hfutils` both run for real, only the HTTP answers are recorded, so a change in either
shows up as a failing test.

```
test/cassettes/
  <module>/<Class>.<test>.json         main cassette of a test (setup, body and teardown)
  <module>/<Class>.<test>.<name>.json  segment of a fixture of that test (see "Fixture groups")
  <module>/<...>.vars.json             variables recorded next to a cassette
  _worlds/<name>.json                  data shared by many tests
  _blobs/<xx>/<sha256>.bin             bodies that are not short text, stored once, shared by all cassettes
  PENDING.txt                          tests that cannot be recorded yet, skipped with a reason
```

## Modes

`pytest --hf-record=<mode>` (or `HFUTILS_VCR_MODE`):

| mode | behaviour |
| --- | --- |
| `none` (default) | replay only. A request the cassette does not know **fails the test**; a test without a cassette cannot reach the network. This is CI. |
| `new` | replay what exists, record what is missing. |
| `rewrite` | delete and record again every cassette the run touches. |
| `live` | no cassettes at all, talk to the real service (`make live`, `hf_live.yml`). |

Recording needs a real `HF_TOKEN`. A test that **fails while recording leaves nothing behind**.

```shell
# record the cassettes of one test file again
HF_TOKEN=hf_xxx pytest test/operate/test_download.py --hf-record=rewrite -m unittest
# or through make
HF_TOKEN=hf_xxx make record RANGE_DIR=operate
```

Record from a machine with a direct, quiet connection to huggingface.co (a CI runner or a cloud node, not a laptop
behind a proxy). After recording, replay (`pytest` without options) and look at `git status`: no token may be in a
cassette (the framework removes `Authorization`, cookies and e-mail addresses, `test/hfvcr` checks it, and
`grep -r "hf_" test/cassettes` is a good last look).

## One recording, every client

Cassettes are recorded with one `huggingface_hub` and replayed by all of them: 0.x speaks through `requests`,
1.x through `httpx`, 2.x through `httpx2`, and VCR.py patches all three. Clients spell the same query differently
(`recursive=False` / `recursive=true`, an optional `expand`), so requests are matched on method, host, path and a
*normalized* query (`test/testings/hfvcr/scrub.py`). A request that really differs between client generations
must be handled there, not by recording once per version.

`HF_HUB_DISABLE_XET=1` is set for every test (`test/testings/hfvcr/env.py`, imported before anything imports
`huggingface_hub`): `hf_xet` is a native client and no Python-level recorder can see it. With Xet off, the bytes of a
Xet-backed file arrive over plain HTTP from the bridge and are recorded like any other download.

## Client generations that differ

A few operations are not the same HTTP conversation on every client: before an upload, `huggingface_hub` 0.x asks the
server things (`paths-info`, `revision/main?expand=xetEnabled`) that 1.x and 2.x never do. For those tests a second cassette
`<name>@hub0.json` is kept next to the default one. On `huggingface_hub` < 1.0 the `@hub0` file answers when it exists; every
other client ignores it.

```shell
# record the 0.x conversation of the upload tests (install a 0.x huggingface_hub first)
HF_TOKEN=hf_xxx pytest test/operate/test_upload.py test/entry/test_upload.py --hf-record=rewrite --hf-variant=hub0 -m unittest
```

## Fixture groups

A test owns one cassette, so ordinary fixtures need nothing. A fixture that wants its own file (and a recorded
random name) opens a *segment*:

```python
@pytest.fixture()
def hf_repo(hf_client, hf_vcr):
    with hf_vcr.segment('repo') as seg:                       # <test>.repo.json
        name = seg.var('name', lambda: f'test_repo_{random_sha1_with_timestamp()}')
        hf_client.create_repo(name, repo_type='dataset', exist_ok=True)
    try:
        yield name
    finally:
        with hf_vcr.segment('repo.cleanup'):                  # <test>.repo.cleanup.json
            hf_client.delete_repo(name, repo_type='dataset')


@pytest.fixture()
def hf_repo_with_files(hf_repo, hf_client, hf_vcr):          # the group: repo -> files -> test body
    with hf_vcr.segment('files'):
        hf_client.upload_file(repo_id=hf_repo, ...)
    yield hf_repo
```

* A segment is a cassette file; segments nest and the innermost one answers.
* `seg.var(name, factory)` runs `factory` while recording and returns the recorded value while replaying, so a
  replay talks about exactly the repository the recording created.
* Within a segment the same request is answered in the order it was recorded (a repository listed before and after
  an upload gives two different answers). `repeats=True` lets one answer serve every repeat; use it only for read-only data.
* `hf_vcr.world('name')` is a segment shared by many tests (`_worlds/`), repeats allowed.

## git, git-lfs and Xet: recorded through a proxy

VCR patches the Python HTTP clients of the test process. `git`, `git-lfs` (subprocesses) and `hf_xet` (a native extension)
speak HTTPS on their own, but they all honour `HTTPS_PROXY` and a per-process CA bundle, so a test marked `@pytest.mark.hf_git`
runs inside a [mitmproxy](https://mitmproxy.org) (`test/testings/hfvcr/proxy.py`):

* flows are stored next to the cassettes, `<test>.git.mitm`, after `mitm_scrub.py` removed credentials, cookies and e-mail
  addresses (git puts the token into the clone URL, so it is in the flows before that);
* **replay is ordered** (one answer per recorded flow: `git push` asks the same URL first without credentials, 401, then with
  them, 200), matches the `Range` header (`hf_xet` reads three ranges of one URL in parallel) but **not the request body** (the
  objects of a `git-lfs` batch request come in a different order on every run), never connects to the real server and refuses a
  request that was not recorded;
* the Python side of the same test stays with the VCR cassettes, so a test can mix both (`test_rollback.py`: the repository and
  its commits through VCR, `git clone` / `git push -f` through the proxy);
* nothing leaves the machine while replaying, and the system trust store is never touched: the CA is only given to the processes
  started inside the test.

`mitmdump` is a separate program because mitmproxy needs a newer Python than the oldest this package supports: it is found
through `$HFUTILS_MITMDUMP` or `PATH` (`uv tool install mitmproxy --python 3.12` is enough). These tests are **skipped, with the
reason printed,** when `mitmdump` or `git-lfs` is missing, and on Windows and macOS: git there uses another TLS backend that may
ignore `GIT_SSL_CAINFO`, which was not verified. CI runs them in three Linux cells. Behind a proxy of your own, set
`HFUTILS_MITM_UPSTREAM=http://host:port` while recording; `HFUTILS_MITM_KEEP=1` keeps the proxy logs of a test session.

## Pending

`PENDING.txt` lists tests whose cassettes could not be recorded; replay mode skips them **with the reason written in the file**,
recording modes run them. Remove an entry when its cassette is committed.

Today that is 55 tests of `test/index` (`test_fetch`, `test_local_fetch`, `test_validate`), `test/entry/test_ils.py`, `test/operate` and
`test/entry` (download, warmup). They read tar archives and index files of the **private** datasets `narugo1992/test_cos5t_tars` and
`narugo1992/test_ds_repo`. The account has reached its private storage limit, and the Hub answers every file download of a private
repository of it with `403 Private repository storage limit reached` (checked 2026-10-27 with the account's own token; the listing APIs
still work). Nothing can be recorded from there until storage is freed, the plan is upgraded or the data is moved to a public
repository; the offsets and hashes that the tests assert belong to those exact files, so equivalent data was not made up.
The code they exercise (mainly `entry/ils.py`, `index/local_fetch.py`, parts of `index/fetch.py`) is therefore not covered in CI.

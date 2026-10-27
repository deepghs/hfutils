"""
Hermetic ``huggingface_hub`` environment for the tests.

**Import this module before anything imports ``huggingface_hub``**: the library reads most of its configuration
once, at import time (``constants.HF_HUB_DISABLE_XET`` for one). ``test/conftest.py`` imports it first for exactly
that reason, and the plugin refuses to run when it came too late.
"""
import atexit
import os
import shutil
import tempfile

HF_HOME = tempfile.mkdtemp(prefix='hfutils-test-hf-home-')
atexit.register(shutil.rmtree, HF_HOME, ignore_errors=True)

os.environ['HF_HOME'] = HF_HOME
os.environ.pop('HF_HUB_CACHE', None)
os.environ.pop('HUGGINGFACE_HUB_CACHE', None)
os.environ.pop('HF_ENDPOINT', None)
os.environ.pop('HF_HUB_OFFLINE', None)
os.environ['HF_HUB_DISABLE_XET'] = '1'  # hf_xet is a native client, nothing at the Python HTTP layer could see it
os.environ['HF_HUB_ENABLE_HF_TRANSFER'] = '0'
os.environ['HF_HUB_DISABLE_TELEMETRY'] = '1'
os.environ['HF_HUB_DISABLE_PROGRESS_BARS'] = '1'

# a developer's proxy must not capture the loopback servers of the framework's own tests
for _name in ('NO_PROXY', 'no_proxy'):
    _hosts = [h for h in os.environ.get(_name, '').split(',') if h]
    os.environ[_name] = ','.join(_hosts + [h for h in ('127.0.0.1', 'localhost') if h not in _hosts])

#: Token handed to the code under test during replay (the recorded ``Authorization`` headers are scrubbed anyway).
REPLAY_TOKEN = 'hf_' + 'R' * 34

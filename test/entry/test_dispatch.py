import pytest
from hbutils.testing import simulate_entry

from hfutils.config.meta import __VERSION__
from hfutils.entry import hfutilscli


@pytest.mark.unittest
class TestEntryDispatch:
    def test_version(self):
        result = simulate_entry(hfutilscli, ['hfutils', '-v'])
        assert result.exitcode == 0, (f'Exitcode: {result.exitcode!r}\n'
                                      f'Error: {result.error!r}\n'
                                      f'========= Stdout =========\n{result.stdout}\n'
                                      f'========= Stderr =========\n{result.stderr}\n')
        assert __VERSION__ in result.stdout

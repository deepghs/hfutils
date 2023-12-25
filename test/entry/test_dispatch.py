import pytest
from hbutils.testing import simulate_entry

from hfutils.config.meta import __VERSION__
from hfutils.entry import hfutilscli


@pytest.mark.unittest
class TestEntryDispatch:
    def test_version(self):
        result = simulate_entry(hfutilscli, ['hfutilscli', '-v'])
        assert result.exitcode == 0
        assert __VERSION__ in result.stdout

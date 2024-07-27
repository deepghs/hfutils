import pytest

from hfutils.utils import number_to_tag


@pytest.mark.unittest
class TestUtilsNumber:
    @pytest.mark.parametrize("number, expected_tag", [
        (0, 'n<1K'),
        (999, 'n<1K'),
        (1000, '1K<n<10K'),
        (9999, '1K<n<10K'),
        (10000, '10K<n<100K'),
        (99999, '10K<n<100K'),
        (100000, '100K<n<1M'),
        (999999, '100K<n<1M'),
        (1000000, '1M<n<10M'),
        (9999999, '1M<n<10M'),
        (10000000, '10M<n<100M'),
        (99999999, '10M<n<100M'),
        (100000000, '100M<n<1B'),
        (999999999, '100M<n<1B'),
        (1000000000, '1B<n<10B'),
        (9999999999, '1B<n<10B'),
        (10000000000, '10B<n<100B'),
        (99999999999, '10B<n<100B'),
        (100000000000, '100B<n<1T'),
        (999999999999, '100B<n<1T'),
        (1000000000000, 'n>1T'),
        (1000000000001, 'n>1T'),
        (float('inf'), 'n>1T'),
    ])
    def test_number_to_tag(self, number, expected_tag):
        assert number_to_tag(number) == expected_tag

    def test_number_to_tag_float(self):
        assert number_to_tag(500.5) == 'n<1K'
        assert number_to_tag(1500.5) == '1K<n<10K'

    def test_number_to_tag_negative(self):
        with pytest.raises(ValueError):
            number_to_tag(-1)

    def test_number_to_tag_invalid(self):
        with pytest.raises(TypeError):
            number_to_tag('invalid')

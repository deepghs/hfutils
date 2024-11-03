"""
This module provides functionality to categorize numeric values into predefined ranges,
returning corresponding tags that represent these ranges. This can be particularly useful
for labeling metadata in applications such as HuggingFace repositories, where numeric
values need to be classified for better understanding and organization.

The ranges are defined in a list of tuples, where each tuple contains a tag and the
minimum and maximum bounds for that range. The primary function in this module is
`number_to_tag`, which takes a numeric value and returns the appropriate tag based
on the defined ranges.
"""

_NUM_TAGS = [
    ('n<1K', 0, 1_000),
    ('1K<n<10K', 1_000, 10_000),
    ('10K<n<100K', 10_000, 100_000),
    ('100K<n<1M', 100_000, 1_000_000),
    ('1M<n<10M', 1_000_000, 10_000_000),
    ('10M<n<100M', 10_000_000, 100_000_000),
    ('100M<n<1B', 100_000_000, 1_000_000_000),
    ('1B<n<10B', 1_000_000_000, 10_000_000_000),
    ('10B<n<100B', 10_000_000_000, 100_000_000_000),
    ('100B<n<1T', 100_000_000_000, 1_000_000_000_000),
    ('n>1T', 1_000_000_000_000, None),
]


def number_to_tag(v):
    """
    Categorize a number into a predefined range and return the corresponding tag for HuggingFace repository metadata.

    :param v: The number to categorize.
    :type v: int or float

    :return: A string tag representing the range in which the number falls.
    :rtype: str

    :raises ValueError: If no matching tag is found for the given number.
    :raises TypeError: If the input value is not numeric type.

    Examples:

        >>> number_to_tag(500)
        'n<1K'
        >>> number_to_tag(5000)
        '1K<n<10K'
        >>> number_to_tag(1000000000000)
        'n>1T'
    """
    if not isinstance(v, (int, float)):
        raise TypeError(f'Invalid type, only numeric types are supported - {v!r}')

    for tag, min_, max_ in _NUM_TAGS:
        if (max_ is not None and min_ <= v < max_) or \
                (max_ is None and min_ <= v):
            return tag

    raise ValueError(f'No tags found for {v!r}')

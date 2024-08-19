import click
import pytest
from hbutils.testing import simulate_entry

from hfutils.entry import hfutilscli


@pytest.mark.unittest
class TestEntryTree:
    def test_simple_tree_1(self):
        result = simulate_entry(hfutilscli, [
            'hfutils', 'tree',
            '-r', 'deepghs/test_nested_dataset',
        ])
        assert result.exitcode == 0
        lines = click.unstyle(result.stdout).strip().splitlines(keepends=False)
        lines = list(filter(bool, lines))
        assert lines == [
            'datasets/deepghs/test_nested_dataset@main/.',
            '├── README.md',
            '├── data.parquet',
            '├── images',
            '│   ├── 20240808',
            '│   │   ├── 20240808015751528545_642b8ce09a5b1543e88cf95e359d39218d6b3ac5__narugo.json',
            '│   │   ├── 20240808015751528545_642b8ce09a5b1543e88cf95e359d39218d6b3ac5__narugo.tar',
            '│   │   ├── 20240808091226009067_be359abd170ee3e1a37d3bda7cdf9ff2490f5380__narugo.json',
            '│   │   └── 20240808091226009067_be359abd170ee3e1a37d3bda7cdf9ff2490f5380__narugo.tar',
            '│   ├── 20240810',
            '│   │   ├── 20240810025407329132_7fbe690d6dca73e971036fbb884eba67d11c68d7__narugo.json',
            '│   │   ├── 20240810025407329132_7fbe690d6dca73e971036fbb884eba67d11c68d7__narugo.tar',
            '│   │   ├── 20240810025642281532_4c13dc63689d93e25a5de44bc9add04ea7d56162__narugo.json',
            '│   │   ├── 20240810025642281532_4c13dc63689d93e25a5de44bc9add04ea7d56162__narugo.tar',
            '│   │   ├── 20240810220450715507_f95017bb0ff97ee35cd878ba11e6c3d5b4eb6e1f__narugo.json',
            '│   │   ├── 20240810220450715507_f95017bb0ff97ee35cd878ba11e6c3d5b4eb6e1f__narugo.tar',
            '│   │   ├── 20240810222438167877_c60911f8922933991a20d190175c9eada582af7b__narugo.json',
            '│   │   └── 20240810222438167877_c60911f8922933991a20d190175c9eada582af7b__narugo.tar',
            '│   └── 20240811',
            '│       ├── 20240811011334412620_ce548cb70673e563ad46a37a75b6c1f933b17292__narugo.json',
            '│       └── 20240811011334412620_ce548cb70673e563ad46a37a75b6c1f933b17292__narugo.tar',
            '├── meta.json',
            '├── samples',
            '│   ├── colored',
            '│   │   ├── 0.webp',
            '│   │   ├── 1.webp',
            '│   │   ├── 2.webp',
            '│   │   ├── 3.webp',
            '│   │   ├── 4.webp',
            '│   │   ├── 5.webp',
            '│   │   ├── 6.webp',
            '│   │   └── 7.webp',
            '│   └── monochrome',
            '│       ├── 0.webp',
            '│       ├── 1.webp',
            '│       ├── 2.webp',
            '│       └── 3.webp',
            '└── unarchived',
            '    └── 20240810222438167877_c60911f8922933991a20d190175c9eada582af7b__narugo.parquet',
        ]

    def test_simple_tree_all(self):
        result = simulate_entry(hfutilscli, [
            'hfutils', 'tree',
            '-r', 'deepghs/test_nested_dataset',
            '--all'
        ])
        assert result.exitcode == 0
        lines = click.unstyle(result.stdout).strip().splitlines(keepends=False)
        lines = list(filter(bool, lines))
        assert lines == [
            'datasets/deepghs/test_nested_dataset@main/.',
            '├── .gitattributes',
            '├── README.md',
            '├── data.parquet',
            '├── images',
            '│   ├── 20240808',
            '│   │   ├── 20240808015751528545_642b8ce09a5b1543e88cf95e359d39218d6b3ac5__narugo.json',
            '│   │   ├── 20240808015751528545_642b8ce09a5b1543e88cf95e359d39218d6b3ac5__narugo.tar',
            '│   │   ├── 20240808091226009067_be359abd170ee3e1a37d3bda7cdf9ff2490f5380__narugo.json',
            '│   │   └── 20240808091226009067_be359abd170ee3e1a37d3bda7cdf9ff2490f5380__narugo.tar',
            '│   ├── 20240810',
            '│   │   ├── 20240810025407329132_7fbe690d6dca73e971036fbb884eba67d11c68d7__narugo.json',
            '│   │   ├── 20240810025407329132_7fbe690d6dca73e971036fbb884eba67d11c68d7__narugo.tar',
            '│   │   ├── 20240810025642281532_4c13dc63689d93e25a5de44bc9add04ea7d56162__narugo.json',
            '│   │   ├── 20240810025642281532_4c13dc63689d93e25a5de44bc9add04ea7d56162__narugo.tar',
            '│   │   ├── 20240810220450715507_f95017bb0ff97ee35cd878ba11e6c3d5b4eb6e1f__narugo.json',
            '│   │   ├── 20240810220450715507_f95017bb0ff97ee35cd878ba11e6c3d5b4eb6e1f__narugo.tar',
            '│   │   ├── 20240810222438167877_c60911f8922933991a20d190175c9eada582af7b__narugo.json',
            '│   │   └── 20240810222438167877_c60911f8922933991a20d190175c9eada582af7b__narugo.tar',
            '│   └── 20240811',
            '│       ├── 20240811011334412620_ce548cb70673e563ad46a37a75b6c1f933b17292__narugo.json',
            '│       └── 20240811011334412620_ce548cb70673e563ad46a37a75b6c1f933b17292__narugo.tar',
            '├── meta.json',
            '├── samples',
            '│   ├── colored',
            '│   │   ├── 0.webp',
            '│   │   ├── 1.webp',
            '│   │   ├── 2.webp',
            '│   │   ├── 3.webp',
            '│   │   ├── 4.webp',
            '│   │   ├── 5.webp',
            '│   │   ├── 6.webp',
            '│   │   └── 7.webp',
            '│   └── monochrome',
            '│       ├── 0.webp',
            '│       ├── 1.webp',
            '│       ├── 2.webp',
            '│       └── 3.webp',
            '└── unarchived',
            '    └── 20240810222438167877_c60911f8922933991a20d190175c9eada582af7b__narugo.parquet'
        ]

    def test_tree_subdir_1(self):
        result = simulate_entry(hfutilscli, [
            'hfutils', 'tree',
            '-r', 'deepghs/test_nested_dataset',
            '-d', 'images'
        ])
        assert result.exitcode == 0
        lines = click.unstyle(result.stdout).strip().splitlines(keepends=False)
        lines = list(filter(bool, lines))
        assert lines == [
            "datasets/deepghs/test_nested_dataset@main/images",
            "├── 20240808",
            "│   ├── 20240808015751528545_642b8ce09a5b1543e88cf95e359d39218d6b3ac5__narugo.json",
            "│   ├── 20240808015751528545_642b8ce09a5b1543e88cf95e359d39218d6b3ac5__narugo.tar",
            "│   ├── 20240808091226009067_be359abd170ee3e1a37d3bda7cdf9ff2490f5380__narugo.json",
            "│   └── 20240808091226009067_be359abd170ee3e1a37d3bda7cdf9ff2490f5380__narugo.tar",
            "├── 20240810",
            "│   ├── 20240810025407329132_7fbe690d6dca73e971036fbb884eba67d11c68d7__narugo.json",
            "│   ├── 20240810025407329132_7fbe690d6dca73e971036fbb884eba67d11c68d7__narugo.tar",
            "│   ├── 20240810025642281532_4c13dc63689d93e25a5de44bc9add04ea7d56162__narugo.json",
            "│   ├── 20240810025642281532_4c13dc63689d93e25a5de44bc9add04ea7d56162__narugo.tar",
            "│   ├── 20240810220450715507_f95017bb0ff97ee35cd878ba11e6c3d5b4eb6e1f__narugo.json",
            "│   ├── 20240810220450715507_f95017bb0ff97ee35cd878ba11e6c3d5b4eb6e1f__narugo.tar",
            "│   ├── 20240810222438167877_c60911f8922933991a20d190175c9eada582af7b__narugo.json",
            "│   └── 20240810222438167877_c60911f8922933991a20d190175c9eada582af7b__narugo.tar",
            "└── 20240811",
            "    ├── 20240811011334412620_ce548cb70673e563ad46a37a75b6c1f933b17292__narugo.json",
            "    └── 20240811011334412620_ce548cb70673e563ad46a37a75b6c1f933b17292__narugo.tar"
        ]

    def test_tree_subdir_2(self):
        result = simulate_entry(hfutilscli, [
            'hfutils', 'tree',
            '-r', 'deepghs/test_nested_dataset',
            '-d', 'samples'
        ])
        assert result.exitcode == 0
        lines = click.unstyle(result.stdout).strip().splitlines(keepends=False)
        lines = list(filter(bool, lines))
        assert lines == [
            "datasets/deepghs/test_nested_dataset@main/samples",
            "├── colored",
            "│   ├── 0.webp",
            "│   ├── 1.webp",
            "│   ├── 2.webp",
            "│   ├── 3.webp",
            "│   ├── 4.webp",
            "│   ├── 5.webp",
            "│   ├── 6.webp",
            "│   └── 7.webp",
            "└── monochrome",
            "    ├── 0.webp",
            "    ├── 1.webp",
            "    ├── 2.webp",
            "    └── 3.webp"
        ]

    def test_tree_subdir_3(self):
        result = simulate_entry(hfutilscli, [
            'hfutils', 'tree',
            '-r', 'deepghs/test_nested_dataset',
            '-d', 'samples/colored'
        ])
        assert result.exitcode == 0
        lines = click.unstyle(result.stdout).strip().splitlines(keepends=False)
        lines = list(filter(bool, lines))
        assert lines == [
            "datasets/deepghs/test_nested_dataset@main/samples/colored",
            "├── 0.webp",
            "├── 1.webp",
            "├── 2.webp",
            "├── 3.webp",
            "├── 4.webp",
            "├── 5.webp",
            "├── 6.webp",
            "└── 7.webp"
        ]

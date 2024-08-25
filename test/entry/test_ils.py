import click
import pytest
from hbutils.testing import simulate_entry

from hfutils.entry import hfutilscli


@pytest.mark.unittest
class TestEntryIls:
    def test_simple_ils_basic(self):
        result = simulate_entry(hfutilscli, [
            'hfutils', 'ils',
            '-r', 'narugo/test_cos5t_tars',
            '-a', 'mashu_skins.tar',
        ])
        assert result.exitcode == 0
        assert click.unstyle(result.stdout).splitlines(keepends=False) == [
            '常夏的泳装Ver_02.png',
            '愚人节.png',
            'Grail_League_1星.png',
            '常夏的泳装.png',
            'Grail_League_3星.png',
            '第4阶段.png',
            'Grail_League_5星.png',
            '.meta.json',
            '第3阶段.png',
            'Grail_League_4星.png',
            '奥特瑙斯_改建型.png',
            '愚人节_奥特瑙斯.png',
            'Grail_League_2星.png',
            'Bright_Voyager.png',
            '第1阶段.png',
            '第2阶段.png',
            '奥特瑙斯.png'
        ]

    def test_ils_desc(self):
        result = simulate_entry(hfutilscli, [
            'hfutils', 'ils',
            '-r', 'narugo/test_cos5t_tars',
            '-a', 'mashu_skins.tar',
            '-o', 'desc',
        ])
        assert result.exitcode == 0
        assert click.unstyle(result.stdout).splitlines(keepends=False) == [
            '奥特瑙斯.png',
            '第2阶段.png',
            '第1阶段.png',
            'Bright_Voyager.png',
            'Grail_League_2星.png',
            '愚人节_奥特瑙斯.png',
            '奥特瑙斯_改建型.png',
            'Grail_League_4星.png',
            '第3阶段.png',
            '.meta.json',
            'Grail_League_5星.png',
            '第4阶段.png',
            'Grail_League_3星.png',
            '常夏的泳装.png',
            'Grail_League_1星.png',
            '愚人节.png',
            '常夏的泳装Ver_02.png'
        ]

    def test_ils_default(self):
        result = simulate_entry(hfutilscli, ['hfutils', 'ils', '-r', 'narugo/test_cos5t_tars', '-a', 'mashu_skins.tar'])
        assert result.exitcode == 0
        assert click.unstyle(result.stdout).splitlines(keepends=False) == [
            "常夏的泳装Ver_02.png",
            "愚人节.png",
            "Grail_League_1星.png",
            "常夏的泳装.png",
            "Grail_League_3星.png",
            "第4阶段.png",
            "Grail_League_5星.png",
            ".meta.json",
            "第3阶段.png",
            "Grail_League_4星.png",
            "奥特瑙斯_改建型.png",
            "愚人节_奥特瑙斯.png",
            "Grail_League_2星.png",
            "Bright_Voyager.png",
            "第1阶段.png",
            "第2阶段.png",
            "奥特瑙斯.png"
        ]

    def test_ils_desc(self):
        result = simulate_entry(hfutilscli,
                                ['hfutils', 'ils', '-r', 'narugo/test_cos5t_tars', '-a', 'mashu_skins.tar', '-o',
                                 'desc'])
        assert result.exitcode == 0
        assert click.unstyle(result.stdout).splitlines(keepends=False) == [
            "奥特瑙斯.png",
            "第2阶段.png",
            "第1阶段.png",
            "Bright_Voyager.png",
            "Grail_League_2星.png",
            "愚人节_奥特瑙斯.png",
            "奥特瑙斯_改建型.png",
            "Grail_League_4星.png",
            "第3阶段.png",
            ".meta.json",
            "Grail_League_5星.png",
            "第4阶段.png",
            "Grail_League_3星.png",
            "常夏的泳装.png",
            "Grail_League_1星.png",
            "愚人节.png",
            "常夏的泳装Ver_02.png"
        ]

    def test_ils_name_asc(self):
        result = simulate_entry(hfutilscli,
                                ['hfutils', 'ils', '-r', 'narugo/test_cos5t_tars', '-a', 'mashu_skins.tar', '-s',
                                 'name'])
        assert result.exitcode == 0
        assert click.unstyle(result.stdout).splitlines(keepends=False) == [
            ".meta.json",
            "Bright_Voyager.png",
            "Grail_League_1星.png",
            "Grail_League_2星.png",
            "Grail_League_3星.png",
            "Grail_League_4星.png",
            "Grail_League_5星.png",
            "奥特瑙斯.png",
            "奥特瑙斯_改建型.png",
            "常夏的泳装.png",
            "常夏的泳装Ver_02.png",
            "愚人节.png",
            "愚人节_奥特瑙斯.png",
            "第1阶段.png",
            "第2阶段.png",
            "第3阶段.png",
            "第4阶段.png"
        ]

    def test_ils_name_desc(self):
        result = simulate_entry(hfutilscli,
                                ['hfutils', 'ils', '-r', 'narugo/test_cos5t_tars', '-a', 'mashu_skins.tar', '-s',
                                 'name', '-o', 'desc'])
        assert result.exitcode == 0
        assert click.unstyle(result.stdout).splitlines(keepends=False) == [
            "第4阶段.png",
            "第3阶段.png",
            "第2阶段.png",
            "第1阶段.png",
            "愚人节_奥特瑙斯.png",
            "愚人节.png",
            "常夏的泳装Ver_02.png",
            "常夏的泳装.png",
            "奥特瑙斯_改建型.png",
            "奥特瑙斯.png",
            "Grail_League_5星.png",
            "Grail_League_4星.png",
            "Grail_League_3星.png",
            "Grail_League_2星.png",
            "Grail_League_1星.png",
            "Bright_Voyager.png",
            ".meta.json"
        ]

    def test_ils_size_asc(self):
        result = simulate_entry(hfutilscli,
                                ['hfutils', 'ils', '-r', 'narugo/test_cos5t_tars', '-a', 'mashu_skins.tar', '-s',
                                 'size'])
        assert result.exitcode == 0
        assert click.unstyle(result.stdout).splitlines(keepends=False) == [
            ".meta.json",
            "愚人节.png",
            "第4阶段.png",
            "常夏的泳装Ver_02.png",
            "第1阶段.png",
            "奥特瑙斯.png",
            "第2阶段.png",
            "第3阶段.png",
            "愚人节_奥特瑙斯.png",
            "奥特瑙斯_改建型.png",
            "Grail_League_1星.png",
            "Grail_League_2星.png",
            "Bright_Voyager.png",
            "常夏的泳装.png",
            "Grail_League_3星.png",
            "Grail_League_4星.png",
            "Grail_League_5星.png"
        ]

    def test_ils_size_desc(self):
        result = simulate_entry(hfutilscli,
                                ['hfutils', 'ils', '-r', 'narugo/test_cos5t_tars', '-a', 'mashu_skins.tar', '-s',
                                 'size', '-o', 'desc'])
        assert result.exitcode == 0
        assert click.unstyle(result.stdout).splitlines(keepends=False) == [
            "Grail_League_5星.png",
            "Grail_League_4星.png",
            "Grail_League_3星.png",
            "常夏的泳装.png",
            "Bright_Voyager.png",
            "Grail_League_2星.png",
            "Grail_League_1星.png",
            "奥特瑙斯_改建型.png",
            "愚人节_奥特瑙斯.png",
            "第3阶段.png",
            "第2阶段.png",
            "奥特瑙斯.png",
            "第1阶段.png",
            "常夏的泳装Ver_02.png",
            "第4阶段.png",
            "愚人节.png",
            ".meta.json"
        ]

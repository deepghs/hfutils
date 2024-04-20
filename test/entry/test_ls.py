import click
import pytest
from hbutils.testing import simulate_entry

from hfutils.entry import hfutilscli


@pytest.mark.unittest
class TestEntryLs:
    def test_simple_ls_1(self):
        result = simulate_entry(hfutilscli, [
            'hfutils', 'ls',
            '-r', 'deepghs/game_character_skins',
            '-d', 'fgo/1'
        ])
        assert result.exitcode == 0
        assert click.unstyle(result.stdout).splitlines(keepends=False) == [
            'Bright_Voyager.png', 'Grail_League_1星.png', 'Grail_League_2星.png', 'Grail_League_3星.png',
            'Grail_League_4星.png', 'Grail_League_5星.png', '奥特瑙斯.png', '奥特瑙斯_改建型.png', '常夏的泳装.png',
            '常夏的泳装Ver_02.png', '愚人节.png', '愚人节_奥特瑙斯.png', '第1阶段.png', '第2阶段.png',
            '第3阶段.png', '第4阶段.png'
        ]

    def test_simple_ls_2(self):
        result = simulate_entry(hfutilscli, [
            'hfutils', 'ls',
            '-r', 'deepghs/game_character_skins',
            '-d', '.'
        ])
        assert result.exitcode == 0
        assert click.unstyle(result.stdout).splitlines(keepends=False) == [
            'arknights', 'azurlane', 'bluearchive', 'fgo', 'genshin', 'girlsfrontline', 'neuralcloud', 'nikke',
            'pathtonowhere', 'starrail']

    def test_simple_ls_2_all(self):
        result = simulate_entry(hfutilscli, [
            'hfutils', 'ls',
            '-r', 'deepghs/game_character_skins',
            '-d', '.', '-a'
        ])
        assert result.exitcode == 0
        assert click.unstyle(result.stdout).splitlines(keepends=False) == [
            'arknights', 'azurlane', 'bluearchive', 'fgo', 'genshin', 'girlsfrontline', 'neuralcloud', 'nikke',
            'pathtonowhere', 'starrail', '.gitattributes']

    def test_simple_3(self):
        result = simulate_entry(hfutilscli, [
            'hfutils', 'ls',
            '-r', 'deepghs/anime_classification',
            '-t', 'model',
            '-d', 'mobilenetv3', '-a'
        ])
        assert result.exitcode == 0
        assert click.unstyle(result.stdout).splitlines(keepends=False) == [
            'meta.json', 'metrics.json', 'model.ckpt', 'model.onnx', 'plot_confusion.png', 'plot_f1_curve.png',
            'plot_p_curve.png', 'plot_pr_curve.png', 'plot_r_curve.png']

    def test_detailed_3(self):
        result = simulate_entry(hfutilscli, [
            'hfutils', 'ls',
            '-r', 'deepghs/anime_classification',
            '-t', 'model',
            '-d', 'mobilenetv3', '-al'
        ])
        assert result.exitcode == 0
        text = click.unstyle(result.stdout)

        assert text.count('dev(narugo): upload old mobile networkds') >= 8
        assert text.count('72a40f25') >= 8
        for file in ['meta.json', 'metrics.json', 'model.ckpt', 'model.onnx', 'plot_confusion.png', 'plot_f1_curve.png',
                     'plot_p_curve.png', 'plot_pr_curve.png', 'plot_r_curve.png']:
            assert file in text, f'File {file!r} not found in:\n{text}'

    def test_detailed_3_root(self):
        result = simulate_entry(hfutilscli, [
            'hfutils', 'ls',
            '-r', 'deepghs/anime_classification',
            '-t', 'model',
            '-d', '.', '-al'
        ])
        assert result.exitcode == 0
        text = click.unstyle(result.stdout)

        assert 'e216b0b2' in text
        assert 'f6683334' in text
        assert 'mobilenetv3_dist' in text
        assert '.gitattributes' in text
        assert 'README.md' in text

    def test_detailed_3_dataset(self):
        result = simulate_entry(hfutilscli, [
            'hfutils', 'ls',
            '-r', 'deepghs/anime_classification',
            '-d', '.', '-al'
        ])
        assert result.exitcode == 0
        text = click.unstyle(result.stdout)

        assert 'anime_cls_v1.zip' in text
        assert 'Upload anime_cls_v1.zip' in text
        assert 'ade036d9' in text

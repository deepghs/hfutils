import click
import pytest
from hbutils.testing import simulate_entry

from hfutils.entry import hfutilscli


@pytest.mark.unittest
class TestEntryIls:
    def test_simple_ils_basic(self):
        result = simulate_entry(hfutilscli, [
            'hfutils', 'ils',
            '-r', 'narugo1992/test_cos5t_tars',
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
            '-r', 'narugo1992/test_cos5t_tars',
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
        result = simulate_entry(hfutilscli, ['hfutils', 'ils', '-r', 'narugo1992/test_cos5t_tars', '-a', 'mashu_skins.tar'])
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
                                ['hfutils', 'ils', '-r', 'narugo1992/test_cos5t_tars', '-a', 'mashu_skins.tar', '-o',
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
                                ['hfutils', 'ils', '-r', 'narugo1992/test_cos5t_tars', '-a', 'mashu_skins.tar', '-s',
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
                                ['hfutils', 'ils', '-r', 'narugo1992/test_cos5t_tars', '-a', 'mashu_skins.tar', '-s',
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
                                ['hfutils', 'ils', '-r', 'narugo1992/test_cos5t_tars', '-a', 'mashu_skins.tar', '-s',
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
                                ['hfutils', 'ils', '-r', 'narugo1992/test_cos5t_tars', '-a', 'mashu_skins.tar', '-s',
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

    def test_ils_detailed_default(self):
        result = simulate_entry(hfutilscli,
                                ['hfutils', 'ils', '-r', 'narugo1992/test_cos5t_tars', '-a', 'mashu_skins.tar', '-l'])
        assert result.exitcode == 0
        assert click.unstyle(result.stdout).splitlines(keepends=False) == [
            "   1536 |     常夏的泳装Ver_02.png 217.118 KiB a5e55da02440901b249f215135fb6dc2745ed7872b310989ac2426408cd2b88d",
            " 225792 |             愚人节.png 152.971 KiB 4e1539e93a82eace5f40293fb64befb85bed7b90174f54bec7e9bbbc98ce55dc",
            " 384000 | Grail_League_1星.png 306.765 KiB 8ff32612cd2668ef0ec448a20dff7153a1a023607a91b9981ef713d587fbff4d",
            " 699904 |           常夏的泳装.png 427.923 KiB e5934bbd6291dedf5fee9a954de537668d5c1080fb8300760f42e539b0c9f8a7",
            "1139712 | Grail_League_3星.png 456.854 KiB c29456d26a1c064cd46a69e8f954f21f1bc6f25dbcca1ec1fad71957a7bb7236",
            "1609216 |            第4阶段.png 214.529 KiB ce5f13bd4ed4ac9e5d3a9883e9b8c68dc7cdc109ec94b5c58816fac8bf4c3ad3",
            "1830912 | Grail_League_5星.png 871.836 KiB a7491adfd729f0cff742ca46571a6093fed91f46a6f28051a18424e3d991daf1",
            "2725376 |          .meta.json   8.758 KiB 4585b01c251a496b73cb231d29fc711cfb1d682a84334d95f6f5b6c1cc5b5222",
            "2736128 |            第3阶段.png 244.402 KiB 6157f95816f92e1815f9156b74efd876d4ebb026d1573da09d9e311de0bbd435",
            "2988032 | Grail_League_4星.png 689.062 KiB c04f1c4e4eead7cb6da1c99fabf39d41890885071e2e9927546ba098d83116e0",
            "3695616 |        奥特瑙斯_改建型.png 250.557 KiB 9ae16e275e4597f6c8e6f09ce0af3e7aa9837821ab2f08483fe8dce8317d8b05",
            "3954176 |        愚人节_奥特瑙斯.png 249.293 KiB 991497fa586f6f4529827e0f8f1f228c20ec9fb507c314ee9d20d47c46f26e89",
            "4211200 | Grail_League_2星.png 329.081 KiB b9ea4cd8340ab0abb926b6e666b3e61d73c44cd1dea2106468d364728704f38e",
            "4550144 |  Bright_Voyager.png 383.661 KiB bf8db943c474cd786b26eb1ec01341270aa5c6f49c9d922a76c153cfef00c9c8",
            "4944896 |            第1阶段.png 227.161 KiB 5b31578f2cc0abf20f25ff35f974d86b67a802f7b931fb74e1e55d723ffe0cfe",
            "5179392 |            第2阶段.png 240.042 KiB 3e22f16436fcfc37cd2c117d8878e592884e8b8f2e2b82c3cfa20c2c37bf7db2",
            "5427200 |            奥特瑙斯.png 235.501 KiB 559f05829d7454054c0ee15baefed8dc48827a2411b2b4d15f1f287b48f62db2"
        ]

    def test_ils_detailed_desc(self):
        result = simulate_entry(hfutilscli,
                                ['hfutils', 'ils', '-r', 'narugo1992/test_cos5t_tars', '-a', 'mashu_skins.tar', '-l', '-o',
                                 'desc'])
        assert result.exitcode == 0
        assert click.unstyle(result.stdout).splitlines(keepends=False) == [
            "5427200 |            奥特瑙斯.png 235.501 KiB 559f05829d7454054c0ee15baefed8dc48827a2411b2b4d15f1f287b48f62db2",
            "5179392 |            第2阶段.png 240.042 KiB 3e22f16436fcfc37cd2c117d8878e592884e8b8f2e2b82c3cfa20c2c37bf7db2",
            "4944896 |            第1阶段.png 227.161 KiB 5b31578f2cc0abf20f25ff35f974d86b67a802f7b931fb74e1e55d723ffe0cfe",
            "4550144 |  Bright_Voyager.png 383.661 KiB bf8db943c474cd786b26eb1ec01341270aa5c6f49c9d922a76c153cfef00c9c8",
            "4211200 | Grail_League_2星.png 329.081 KiB b9ea4cd8340ab0abb926b6e666b3e61d73c44cd1dea2106468d364728704f38e",
            "3954176 |        愚人节_奥特瑙斯.png 249.293 KiB 991497fa586f6f4529827e0f8f1f228c20ec9fb507c314ee9d20d47c46f26e89",
            "3695616 |        奥特瑙斯_改建型.png 250.557 KiB 9ae16e275e4597f6c8e6f09ce0af3e7aa9837821ab2f08483fe8dce8317d8b05",
            "2988032 | Grail_League_4星.png 689.062 KiB c04f1c4e4eead7cb6da1c99fabf39d41890885071e2e9927546ba098d83116e0",
            "2736128 |            第3阶段.png 244.402 KiB 6157f95816f92e1815f9156b74efd876d4ebb026d1573da09d9e311de0bbd435",
            "2725376 |          .meta.json   8.758 KiB 4585b01c251a496b73cb231d29fc711cfb1d682a84334d95f6f5b6c1cc5b5222",
            "1830912 | Grail_League_5星.png 871.836 KiB a7491adfd729f0cff742ca46571a6093fed91f46a6f28051a18424e3d991daf1",
            "1609216 |            第4阶段.png 214.529 KiB ce5f13bd4ed4ac9e5d3a9883e9b8c68dc7cdc109ec94b5c58816fac8bf4c3ad3",
            "1139712 | Grail_League_3星.png 456.854 KiB c29456d26a1c064cd46a69e8f954f21f1bc6f25dbcca1ec1fad71957a7bb7236",
            " 699904 |           常夏的泳装.png 427.923 KiB e5934bbd6291dedf5fee9a954de537668d5c1080fb8300760f42e539b0c9f8a7",
            " 384000 | Grail_League_1星.png 306.765 KiB 8ff32612cd2668ef0ec448a20dff7153a1a023607a91b9981ef713d587fbff4d",
            " 225792 |             愚人节.png 152.971 KiB 4e1539e93a82eace5f40293fb64befb85bed7b90174f54bec7e9bbbc98ce55dc",
            "   1536 |     常夏的泳装Ver_02.png 217.118 KiB a5e55da02440901b249f215135fb6dc2745ed7872b310989ac2426408cd2b88d"
        ]

    def test_ils_detailed_name_asc(self):
        result = simulate_entry(hfutilscli,
                                ['hfutils', 'ils', '-r', 'narugo1992/test_cos5t_tars', '-a', 'mashu_skins.tar', '-l', '-s',
                                 'name'])
        assert result.exitcode == 0
        assert click.unstyle(result.stdout).splitlines(keepends=False) == [
            "2725376 |          .meta.json   8.758 KiB 4585b01c251a496b73cb231d29fc711cfb1d682a84334d95f6f5b6c1cc5b5222",
            "4550144 |  Bright_Voyager.png 383.661 KiB bf8db943c474cd786b26eb1ec01341270aa5c6f49c9d922a76c153cfef00c9c8",
            " 384000 | Grail_League_1星.png 306.765 KiB 8ff32612cd2668ef0ec448a20dff7153a1a023607a91b9981ef713d587fbff4d",
            "4211200 | Grail_League_2星.png 329.081 KiB b9ea4cd8340ab0abb926b6e666b3e61d73c44cd1dea2106468d364728704f38e",
            "1139712 | Grail_League_3星.png 456.854 KiB c29456d26a1c064cd46a69e8f954f21f1bc6f25dbcca1ec1fad71957a7bb7236",
            "2988032 | Grail_League_4星.png 689.062 KiB c04f1c4e4eead7cb6da1c99fabf39d41890885071e2e9927546ba098d83116e0",
            "1830912 | Grail_League_5星.png 871.836 KiB a7491adfd729f0cff742ca46571a6093fed91f46a6f28051a18424e3d991daf1",
            "5427200 |            奥特瑙斯.png 235.501 KiB 559f05829d7454054c0ee15baefed8dc48827a2411b2b4d15f1f287b48f62db2",
            "3695616 |        奥特瑙斯_改建型.png 250.557 KiB 9ae16e275e4597f6c8e6f09ce0af3e7aa9837821ab2f08483fe8dce8317d8b05",
            " 699904 |           常夏的泳装.png 427.923 KiB e5934bbd6291dedf5fee9a954de537668d5c1080fb8300760f42e539b0c9f8a7",
            "   1536 |     常夏的泳装Ver_02.png 217.118 KiB a5e55da02440901b249f215135fb6dc2745ed7872b310989ac2426408cd2b88d",
            " 225792 |             愚人节.png 152.971 KiB 4e1539e93a82eace5f40293fb64befb85bed7b90174f54bec7e9bbbc98ce55dc",
            "3954176 |        愚人节_奥特瑙斯.png 249.293 KiB 991497fa586f6f4529827e0f8f1f228c20ec9fb507c314ee9d20d47c46f26e89",
            "4944896 |            第1阶段.png 227.161 KiB 5b31578f2cc0abf20f25ff35f974d86b67a802f7b931fb74e1e55d723ffe0cfe",
            "5179392 |            第2阶段.png 240.042 KiB 3e22f16436fcfc37cd2c117d8878e592884e8b8f2e2b82c3cfa20c2c37bf7db2",
            "2736128 |            第3阶段.png 244.402 KiB 6157f95816f92e1815f9156b74efd876d4ebb026d1573da09d9e311de0bbd435",
            "1609216 |            第4阶段.png 214.529 KiB ce5f13bd4ed4ac9e5d3a9883e9b8c68dc7cdc109ec94b5c58816fac8bf4c3ad3"
        ]

    def test_ils_detailed_name_desc(self):
        result = simulate_entry(hfutilscli,
                                ['hfutils', 'ils', '-r', 'narugo1992/test_cos5t_tars', '-a', 'mashu_skins.tar', '-l', '-s',
                                 'name', '-o', 'desc'])
        assert result.exitcode == 0
        assert click.unstyle(result.stdout).splitlines(keepends=False) == [
            "1609216 |            第4阶段.png 214.529 KiB ce5f13bd4ed4ac9e5d3a9883e9b8c68dc7cdc109ec94b5c58816fac8bf4c3ad3",
            "2736128 |            第3阶段.png 244.402 KiB 6157f95816f92e1815f9156b74efd876d4ebb026d1573da09d9e311de0bbd435",
            "5179392 |            第2阶段.png 240.042 KiB 3e22f16436fcfc37cd2c117d8878e592884e8b8f2e2b82c3cfa20c2c37bf7db2",
            "4944896 |            第1阶段.png 227.161 KiB 5b31578f2cc0abf20f25ff35f974d86b67a802f7b931fb74e1e55d723ffe0cfe",
            "3954176 |        愚人节_奥特瑙斯.png 249.293 KiB 991497fa586f6f4529827e0f8f1f228c20ec9fb507c314ee9d20d47c46f26e89",
            " 225792 |             愚人节.png 152.971 KiB 4e1539e93a82eace5f40293fb64befb85bed7b90174f54bec7e9bbbc98ce55dc",
            "   1536 |     常夏的泳装Ver_02.png 217.118 KiB a5e55da02440901b249f215135fb6dc2745ed7872b310989ac2426408cd2b88d",
            " 699904 |           常夏的泳装.png 427.923 KiB e5934bbd6291dedf5fee9a954de537668d5c1080fb8300760f42e539b0c9f8a7",
            "3695616 |        奥特瑙斯_改建型.png 250.557 KiB 9ae16e275e4597f6c8e6f09ce0af3e7aa9837821ab2f08483fe8dce8317d8b05",
            "5427200 |            奥特瑙斯.png 235.501 KiB 559f05829d7454054c0ee15baefed8dc48827a2411b2b4d15f1f287b48f62db2",
            "1830912 | Grail_League_5星.png 871.836 KiB a7491adfd729f0cff742ca46571a6093fed91f46a6f28051a18424e3d991daf1",
            "2988032 | Grail_League_4星.png 689.062 KiB c04f1c4e4eead7cb6da1c99fabf39d41890885071e2e9927546ba098d83116e0",
            "1139712 | Grail_League_3星.png 456.854 KiB c29456d26a1c064cd46a69e8f954f21f1bc6f25dbcca1ec1fad71957a7bb7236",
            "4211200 | Grail_League_2星.png 329.081 KiB b9ea4cd8340ab0abb926b6e666b3e61d73c44cd1dea2106468d364728704f38e",
            " 384000 | Grail_League_1星.png 306.765 KiB 8ff32612cd2668ef0ec448a20dff7153a1a023607a91b9981ef713d587fbff4d",
            "4550144 |  Bright_Voyager.png 383.661 KiB bf8db943c474cd786b26eb1ec01341270aa5c6f49c9d922a76c153cfef00c9c8",
            "2725376 |          .meta.json   8.758 KiB 4585b01c251a496b73cb231d29fc711cfb1d682a84334d95f6f5b6c1cc5b5222"
        ]

    def test_ils_detailed_size_asc(self):
        result = simulate_entry(hfutilscli,
                                ['hfutils', 'ils', '-r', 'narugo1992/test_cos5t_tars', '-a', 'mashu_skins.tar', '-l', '-s',
                                 'size'])
        assert result.exitcode == 0
        assert click.unstyle(result.stdout).splitlines(keepends=False) == [
            "2725376 |          .meta.json   8.758 KiB 4585b01c251a496b73cb231d29fc711cfb1d682a84334d95f6f5b6c1cc5b5222",
            " 225792 |             愚人节.png 152.971 KiB 4e1539e93a82eace5f40293fb64befb85bed7b90174f54bec7e9bbbc98ce55dc",
            "1609216 |            第4阶段.png 214.529 KiB ce5f13bd4ed4ac9e5d3a9883e9b8c68dc7cdc109ec94b5c58816fac8bf4c3ad3",
            "   1536 |     常夏的泳装Ver_02.png 217.118 KiB a5e55da02440901b249f215135fb6dc2745ed7872b310989ac2426408cd2b88d",
            "4944896 |            第1阶段.png 227.161 KiB 5b31578f2cc0abf20f25ff35f974d86b67a802f7b931fb74e1e55d723ffe0cfe",
            "5427200 |            奥特瑙斯.png 235.501 KiB 559f05829d7454054c0ee15baefed8dc48827a2411b2b4d15f1f287b48f62db2",
            "5179392 |            第2阶段.png 240.042 KiB 3e22f16436fcfc37cd2c117d8878e592884e8b8f2e2b82c3cfa20c2c37bf7db2",
            "2736128 |            第3阶段.png 244.402 KiB 6157f95816f92e1815f9156b74efd876d4ebb026d1573da09d9e311de0bbd435",
            "3954176 |        愚人节_奥特瑙斯.png 249.293 KiB 991497fa586f6f4529827e0f8f1f228c20ec9fb507c314ee9d20d47c46f26e89",
            "3695616 |        奥特瑙斯_改建型.png 250.557 KiB 9ae16e275e4597f6c8e6f09ce0af3e7aa9837821ab2f08483fe8dce8317d8b05",
            " 384000 | Grail_League_1星.png 306.765 KiB 8ff32612cd2668ef0ec448a20dff7153a1a023607a91b9981ef713d587fbff4d",
            "4211200 | Grail_League_2星.png 329.081 KiB b9ea4cd8340ab0abb926b6e666b3e61d73c44cd1dea2106468d364728704f38e",
            "4550144 |  Bright_Voyager.png 383.661 KiB bf8db943c474cd786b26eb1ec01341270aa5c6f49c9d922a76c153cfef00c9c8",
            " 699904 |           常夏的泳装.png 427.923 KiB e5934bbd6291dedf5fee9a954de537668d5c1080fb8300760f42e539b0c9f8a7",
            "1139712 | Grail_League_3星.png 456.854 KiB c29456d26a1c064cd46a69e8f954f21f1bc6f25dbcca1ec1fad71957a7bb7236",
            "2988032 | Grail_League_4星.png 689.062 KiB c04f1c4e4eead7cb6da1c99fabf39d41890885071e2e9927546ba098d83116e0",
            "1830912 | Grail_League_5星.png 871.836 KiB a7491adfd729f0cff742ca46571a6093fed91f46a6f28051a18424e3d991daf1"
        ]

    def test_ils_detailed_size_desc(self):
        result = simulate_entry(hfutilscli,
                                ['hfutils', 'ils', '-r', 'narugo1992/test_cos5t_tars', '-a', 'mashu_skins.tar', '-l', '-s',
                                 'size', '-o', 'desc'])
        assert result.exitcode == 0
        assert click.unstyle(result.stdout).splitlines(keepends=False) == [
            "1830912 | Grail_League_5星.png 871.836 KiB a7491adfd729f0cff742ca46571a6093fed91f46a6f28051a18424e3d991daf1",
            "2988032 | Grail_League_4星.png 689.062 KiB c04f1c4e4eead7cb6da1c99fabf39d41890885071e2e9927546ba098d83116e0",
            "1139712 | Grail_League_3星.png 456.854 KiB c29456d26a1c064cd46a69e8f954f21f1bc6f25dbcca1ec1fad71957a7bb7236",
            " 699904 |           常夏的泳装.png 427.923 KiB e5934bbd6291dedf5fee9a954de537668d5c1080fb8300760f42e539b0c9f8a7",
            "4550144 |  Bright_Voyager.png 383.661 KiB bf8db943c474cd786b26eb1ec01341270aa5c6f49c9d922a76c153cfef00c9c8",
            "4211200 | Grail_League_2星.png 329.081 KiB b9ea4cd8340ab0abb926b6e666b3e61d73c44cd1dea2106468d364728704f38e",
            " 384000 | Grail_League_1星.png 306.765 KiB 8ff32612cd2668ef0ec448a20dff7153a1a023607a91b9981ef713d587fbff4d",
            "3695616 |        奥特瑙斯_改建型.png 250.557 KiB 9ae16e275e4597f6c8e6f09ce0af3e7aa9837821ab2f08483fe8dce8317d8b05",
            "3954176 |        愚人节_奥特瑙斯.png 249.293 KiB 991497fa586f6f4529827e0f8f1f228c20ec9fb507c314ee9d20d47c46f26e89",
            "2736128 |            第3阶段.png 244.402 KiB 6157f95816f92e1815f9156b74efd876d4ebb026d1573da09d9e311de0bbd435",
            "5179392 |            第2阶段.png 240.042 KiB 3e22f16436fcfc37cd2c117d8878e592884e8b8f2e2b82c3cfa20c2c37bf7db2",
            "5427200 |            奥特瑙斯.png 235.501 KiB 559f05829d7454054c0ee15baefed8dc48827a2411b2b4d15f1f287b48f62db2",
            "4944896 |            第1阶段.png 227.161 KiB 5b31578f2cc0abf20f25ff35f974d86b67a802f7b931fb74e1e55d723ffe0cfe",
            "   1536 |     常夏的泳装Ver_02.png 217.118 KiB a5e55da02440901b249f215135fb6dc2745ed7872b310989ac2426408cd2b88d",
            "1609216 |            第4阶段.png 214.529 KiB ce5f13bd4ed4ac9e5d3a9883e9b8c68dc7cdc109ec94b5c58816fac8bf4c3ad3",
            " 225792 |             愚人节.png 152.971 KiB 4e1539e93a82eace5f40293fb64befb85bed7b90174f54bec7e9bbbc98ce55dc",
            "2725376 |          .meta.json   8.758 KiB 4585b01c251a496b73cb231d29fc711cfb1d682a84334d95f6f5b6c1cc5b5222"
        ]

    def test_ils_information(self):
        result = simulate_entry(hfutilscli,
                                ['hfutils', 'ils', '-r', 'narugo1992/test_cos5t_tars', '-a', 'mashu_skins.tar', '-I'])
        assert result.exitcode == 0
        assert click.unstyle(result.stdout).splitlines(keepends=False) == [
            "Repo ID: narugo1992/test_cos5t_tars",
            "Repo Type: dataset",
            "Revision: main",
            "Archive File: mashu_skins.tar",
            "",
            "File Size: 5.410 MiB (5672960 Bytes)",
            "Native Hash: a55942a154b97580d4ffdae1219c95120ea94294",
            "LFS Hash: 6e7d17af49c7502e8045575f214cd9229a5b0b842d68591a7a5d9aee1448f478",
            "Files: 17 files",
            "  Image Files: 16 files",
            "  Data Files: 1 file",
            "File Extensions:",
            "  .png : 16 files",
            "  .json : 1 file",
            "Total Size: 5.376 MiB",
            "  Average File Size: 323.854 KiB",
            "  Median File Size: 249.293 KiB",
            "  Smallest File Size: 8.758 KiB",
            "  Largest File Size: 871.836 KiB",
            "  Standard Deviation: 202.998 KiB",
            "Quartiles:",
            "  Q1 (25th Percentile): 227.161 KiB",
            "  Q2 (50th Percentile, Median): 249.293 KiB",
            "  Q3 (75th Percentile): 383.661 KiB",
            "  Interquartile Range (IQR): 156.500 KiB",
            "",
            "Status: Up-To-Date"
        ]

    def test_ils_information_not_match(self):
        result = simulate_entry(hfutilscli,
                                ['hfutils', 'ils', '-r', 'narugo1992/test_cos5t_tars', '-a', 'mashu_skins.tar', '-I', '-i',
                                 'ex3.json'])
        assert result.exitcode == 0
        assert click.unstyle(result.stdout).splitlines(keepends=False) == [
            "Repo ID: narugo1992/test_cos5t_tars",
            "Repo Type: dataset",
            "Revision: main",
            "Archive File: mashu_skins.tar",
            "Index File: ex3.json",
            "",
            "File Size: 24.482 MiB (25671680 Bytes)",
            "Native Hash: f7f756e3f5e744cc94197cc669c409fd8990deba",
            "LFS Hash: abb016a5115ec2f18771b42128f50f2c96caace5cf9e84d1c342a9ab8da93e0e",
            "Files: 295 files",
            "  Image Files: 295 files",
            "File Extensions:",
            "  .jpg : 295 files",
            "Total Size: 23.974 MiB",
            "  Average File Size: 83.218 KiB",
            "  Median File Size: 79.722 KiB",
            "  Smallest File Size: 32.238 KiB",
            "  Largest File Size: 197.258 KiB",
            "  Standard Deviation: 25.068 KiB",
            "Quartiles:",
            "  Q1 (25th Percentile): 64.862 KiB",
            "  Q2 (50th Percentile, Median): 79.722 KiB",
            "  Q3 (75th Percentile): 98.960 KiB",
            "  Interquartile Range (IQR): 34.098 KiB",
            "",
            "Status: Outdated",
            "Index file is recommended to get refreshed."
        ]

    def test_ils_information_sep(self):
        result = simulate_entry(hfutilscli,
                                ['hfutils', 'ils', '-r', 'nyanko7/danbooru2023', '-a', 'original/data-0000.tar', '-I',
                                 '--idx_repository', 'deepghs/danbooru2023_index', '-i', 'original/data-0000.json'])
        assert result.exitcode == 0
        assert click.unstyle(result.stdout).splitlines(keepends=False) == [
            "Repo ID: nyanko7/danbooru2023",
            "Index Repo ID: deepghs/danbooru2023_index",
            "Repo Type: dataset",
            "Revision: main",
            "Archive File: original/data-0000.tar",
            "Index File: original/data-0000.json",
            "",
            "File Size: 7.592 GiB (8151715840 Bytes)",
            "Native Hash: 334e3b11928649d8d2b8fb79d6b281dd72d704d1",
            "LFS Hash: f2b1d0650c36af4d20d933b4068d2a7b88f79e4d39bb8776d423fbb40f9e055e",
            "Files: 6766 files",
            "  Image Files: 6729 files",
            "  Archive/Compressed Files: 9 files",
            "  Other Files: 28 files",
            "File Extensions:",
            "  .jpg : 5040 files",
            "  .png : 1657 files",
            "  .gif : 28 files",
            "  .mp4 : 26 files",
            "  .zip : 9 files",
            "  .webp : 3 files",
            "  . : 1 file",
            "  .jpeg : 1 file",
            "  .swf : 1 file",
            "Total Size: 7.587 GiB",
            "  Average File Size: 1.148 MiB",
            "  Median File Size: 504.214 KiB",
            "  Smallest File Size: 0.000 Bit",
            "  Largest File Size: 41.124 MiB",
            "  Standard Deviation: 2.147 MiB",
            "Quartiles:",
            "  Q1 (25th Percentile): 229.165 KiB",
            "  Q2 (50th Percentile, Median): 504.214 KiB",
            "  Q3 (75th Percentile): 1.111 MiB",
            "  Interquartile Range (IQR): 908.403 KiB",
            "",
            "Status: Up-To-Date"
        ]

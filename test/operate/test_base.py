import pytest

from hfutils.operate import list_files_in_repository

should_not_exists = [
    '.gitignore',
    '.gitattributes',
]


@pytest.mark.unittest
class TestOperateBase:
    def test_list_files_in_repository(self):
        files = list_files_in_repository('deepghs/highres_datasets')
        should_exists = [
            'README.md',
            'sankaku_highres_uncensored_webp_42692.zip',
            'unsplash_elite_webp_q80.zip',
            'yande_highres_webp_36772.zip'
        ]
        assert (set(should_exists) & set(files)) == set(should_exists)
        assert not (set(should_not_exists) & set(files))

    def test_list_files_in_repository_no_ignore(self):
        files = list_files_in_repository('deepghs/highres_datasets', ignore_patterns=[])
        should_exists = [
            '.gitattributes',
            'README.md',
            'sankaku_highres_uncensored_webp_42692.zip',
            'unsplash_elite_webp_q80.zip',
            'yande_highres_webp_36772.zip'
        ]
        assert (set(should_exists) & set(files)) == set(should_exists)

    def test_list_files_in_repository_model(self):
        files = list_files_in_repository('deepghs/anime_real_cls', repo_type='model')
        should_exists = [
            'README.md',
            'caformer_s36_v0/meta.json',
            'caformer_s36_v0/metrics.json',
            'caformer_s36_v0/model.ckpt',
            'caformer_s36_v0/model.onnx',
            'caformer_s36_v0/plot_confusion.png',
            'caformer_s36_v0/plot_f1_curve.png',
            'caformer_s36_v0/plot_p_curve.png',
            'caformer_s36_v0/plot_pr_curve.png',
            'caformer_s36_v0/plot_r_curve.png',
            'caformer_s36_v0/plot_roc_curve.png',
            'caformer_s36_v0/plot_sample_anime.png',
            'caformer_s36_v0/plot_sample_real.png',
            'mobilenetv3_v0_dist/meta.json',
            'mobilenetv3_v0_dist/metrics.json',
            'mobilenetv3_v0_dist/model.ckpt',
            'mobilenetv3_v0_dist/model.onnx',
            'mobilenetv3_v0_dist/plot_confusion.png',
            'mobilenetv3_v0_dist/plot_f1_curve.png',
            'mobilenetv3_v0_dist/plot_p_curve.png',
            'mobilenetv3_v0_dist/plot_pr_curve.png',
            'mobilenetv3_v0_dist/plot_r_curve.png',
            'mobilenetv3_v0_dist/plot_roc_curve.png',
            'mobilenetv3_v0_dist/plot_sample_anime.png',
            'mobilenetv3_v0_dist/plot_sample_real.png'
        ]
        assert (set(should_exists) & set(files)) == set(should_exists)
        assert not (set(should_not_exists) & set(files))

        should_not_exists_2 = ['mobilenetv3_v0_dist', 'caformer_s36_v0']
        assert not (set(should_not_exists_2) & set(files))

    def test_list_files_in_repository_subdir(self):
        files = list_files_in_repository('deepghs/anime_real_cls', repo_type='model', subdir='caformer_s36_v0')
        should_exists = [
            'meta.json',
            'metrics.json',
            'model.ckpt',
            'model.onnx',
            'plot_confusion.png',
            'plot_f1_curve.png',
            'plot_p_curve.png',
            'plot_pr_curve.png',
            'plot_r_curve.png',
            'plot_roc_curve.png',
            'plot_sample_anime.png',
            'plot_sample_real.png'
        ]
        assert (set(should_exists) & set(files)) == set(should_exists)
        assert not (set(should_not_exists) & set(files))

        files = list_files_in_repository('deepghs/anime_real_cls', repo_type='model', subdir='caformer_s36sdkflds')
        assert files == []

    def test_list_files_in_repository_space(self):
        files = list_files_in_repository('deepghs/nsfw_prediction', repo_type='space')
        should_exists = [
            'README.md',
            'app.py',
            'requirements.txt',
        ]
        assert (set(should_exists) & set(files)) == set(should_exists)
        assert not (set(should_not_exists) & set(files))

    def test_list_files_in_repository_failed(self):
        with pytest.raises(ValueError):
            list_files_in_repository('deepghs/highres_datasets', repo_type='fff')

    def test_list_files_in_repository_repo_not_exist(self):
        assert list_files_in_repository('deepghs/highres_datasets', repo_type='model') == []

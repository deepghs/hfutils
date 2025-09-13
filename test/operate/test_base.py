import pytest
from huggingface_hub.errors import RepositoryNotFoundError
from huggingface_hub.hf_api import RepoFile
from natsort import natsorted

from hfutils.operate import list_files_in_repository, list_all_with_pattern, hf_repo_glob

should_not_exists = [
    '.gitignore',
    '.gitattributes',
]


@pytest.mark.unittest
class TestOperateBase:
    def test_hf_repo_glob(self):
        repo_files = hf_repo_glob('deepghs/anime_real_cls', repo_type='model')
        for repo_file in repo_files:
            assert isinstance(repo_file, RepoFile)
        files = [repo_file.path for repo_file in repo_files]
        should_exists = [
            '.gitattributes',
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

        should_not_exists_2 = ['mobilenetv3_v0_dist', 'caformer_s36_v0']
        assert not (set(should_not_exists_2) & set(files))

    def test_hf_repo_glob_with_pattern(self):
        repo_files = hf_repo_glob('deepghs/anime_real_cls', repo_type='model', pattern=['*', '!.git*'])
        for repo_file in repo_files:
            assert isinstance(repo_file, RepoFile)
        files = [repo_file.path for repo_file in repo_files]
        should_exists = [
            'README.md',
        ]
        assert (set(should_exists) & set(files)) == set(should_exists)
        assert not (set(should_not_exists) & set(files))

        should_not_exists_2 = [
            'mobilenetv3_v0_dist',
            'caformer_s36_v0',
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
        assert not (set(should_not_exists_2) & set(files))

    def test_hf_repo_glob_return_path(self):
        files = hf_repo_glob('deepghs/anime_real_cls', repo_type='model', return_path=True)
        should_exists = [
            '.gitattributes',
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

        should_not_exists_2 = ['mobilenetv3_v0_dist', 'caformer_s36_v0']
        assert not (set(should_not_exists_2) & set(files))

    def test_hf_repo_glob_return_path_with_pattern(self):
        files = hf_repo_glob('deepghs/anime_real_cls', repo_type='model',
                             pattern=['*', '!.git*'], return_path=True)
        should_exists = [
            'README.md',
        ]
        assert (set(should_exists) & set(files)) == set(should_exists)
        assert not (set(should_not_exists) & set(files))

        should_not_exists_2 = [
            'mobilenetv3_v0_dist',
            'caformer_s36_v0',
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
        assert not (set(should_not_exists_2) & set(files))

    def test_hf_repo_glob_repo_not_exist(self):
        assert hf_repo_glob('deepghs/highres_datasets', repo_type='model') == []

    def test_hf_repo_glob_repo_not_exist_raise(self):
        with pytest.raises(RepositoryNotFoundError):
            hf_repo_glob('deepghs/highres_datasets', repo_type='model',
                         raise_when_base_not_exist=True)

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

    def test_list_files_in_repository_revision(self):
        files = list_files_in_repository(
            repo_id='narugo1992/test_ds_repo',
            repo_type='dataset',
            revision='another_branch',
        )
        should_exists = ['cloc.sh', 'raw_text', 'surtr_dataset.zip', 'surtr_dataset.zip_x']
        assert (set(should_exists) & set(files)) == set(should_exists)
        assert not (set(should_not_exists) & set(files))

    def test_list_files_in_repository_no_ignore(self):
        files = list_files_in_repository('deepghs/highres_datasets', pattern=['*'])
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

    def test_list_files_in_repository_model_low(self):
        files = list_files_in_repository(
            'deepghs/anime_real_cls', repo_type='model',
            pattern=['*', '!.git*'],
        )
        should_exists = [
            'README.md',
        ]
        assert (set(should_exists) & set(files)) == set(should_exists)
        assert not (set(should_not_exists) & set(files))

        should_not_exists_2 = [
            'mobilenetv3_v0_dist',
            'caformer_s36_v0',
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

    def test_list_files_in_repository_large(self):
        files = list_files_in_repository('deepghs/danbooru_newest', repo_type='dataset', pattern='**/*.tar')
        files = natsorted(files)
        assert files == [
            f'images/0{i:03d}.tar'
            for i in range(1000)
        ]

    def test_list_files_in_repository_repo_not_exist(self):
        assert list_files_in_repository('deepghs/highres_datasets', repo_type='model') == []

    def test_list_all_with_pattern(self):
        vs = natsorted([
            item.path for item in
            list_all_with_pattern(
                'deepghs/danbooru_newest',
                repo_type='dataset',
                pattern='images/*',
            )
        ])
        assert vs == natsorted([
            *[f'images/0{i:03d}.tar' for i in range(1000)],
            *[f'images/0{i:03d}.json' for i in range(1000)],
        ])

    def test_list_all_with_pattern_with_large_startup_deprecated(self):
        vs = natsorted([
            item.path for item in
            list_all_with_pattern(
                'deepghs/danbooru_newest',
                repo_type='dataset',
                pattern='images/*',
                # startup_batch=1500,
            )
        ])
        assert vs == natsorted([
            *[f'images/0{i:03d}.tar' for i in range(1000)],
            *[f'images/0{i:03d}.json' for i in range(1000)],
        ])

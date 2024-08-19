from pathlib import Path

import pytest

from hfutils.utils.model import is_model_file


@pytest.mark.unittest
class TestUtilsModels:
    @pytest.mark.parametrize("filename, expected", [
        ("model.ckpt", True),
        ("model.pt", True),
        ("model.pth", True),
        ("model.safetensors", True),
        ("model.onnx", True),
        ("model.h5", True),
        ("model.tflite", True),
        ("model.pkl", True),
        ("model.bin", True),
        ("model.params", True),
        ("model.pdparams", True),
        ("model.keras", True),
        ("model.weights", True),
        ("model.pmml", True),
        ("model.gguf", True),
        ("model.ggml", True),
        ("model.q4_0", True),
        ("model.q4_1", True),
        ("model.q5_0", True),
        ("model.q5_1", True),
        ("model.q8_0", True),
        ("model.qnt", True),
        ("model.int8", True),
        ("model.fp16", True),
        ("model.bk", True),
        ("model.engine", True),
        ("model.plan", True),
        ("model.trt", True),
        ("model.torchscript", True),
        ("model.pdiparams", True),
        ("model.pdopt", True),
        ("model.nb", True),
        ("model.mnn", True),
        ("model.ncnn", True),
        ("model.om", True),
        ("model.rknn", True),
        ("model.xmodel", True),
        ("model.kmodel", True),
        ("data.txt", False),
        ("image.jpg", False),
        ("archive.zip", False),
    ])
    def test_common_model_extensions(self, filename, expected):
        assert is_model_file(filename) == expected

    @pytest.mark.parametrize("filename, expected", [
        ("model-00001-of-00002", True),
        ("model.bin.1", True),
        ("model.part.0", True),
        ("model_part_0", True),
        ("model-shard1", True),
        ("model_01", False),
        ("model-part", False),
    ])
    def test_shard_patterns(self, filename, expected):
        assert is_model_file(filename) == expected

    @pytest.mark.parametrize("filename, expected", [
        ("pytorch_model.bin", True),
        ("tf_model.h5", True),
        ("model.ckpt", True),
        ("flax_model.msgpack", True),
        ("model.safetensors", True),
        ("tokenizer.json", False),
        ("config.json", False),
    ])
    def test_huggingface_patterns(self, filename, expected):
        assert is_model_file(filename) == expected

    @pytest.mark.parametrize("filename, expected", [
        ("model_quant.gguf", True),
        ("model_quantized.q4_0", True),
        ("model_int8.q5_1", True),
        ("model_fp16.q8_0", True),
        ("model_quantized.qnt", True),
        ("model_int8.int8", True),
        ("model_fp16.fp16", True),
        ("model_float32.pth", True),
    ])
    def test_quantized_patterns(self, filename, expected):
        assert is_model_file(filename) == expected

    def test_pathlib_input(self):
        assert is_model_file(Path("/home/user/model.pt"))
        assert not is_model_file(Path("/home/user/data.txt"))

    def test_invalid_input(self):
        with pytest.raises(TypeError):
            is_model_file(123)

    def test_empty_string(self):
        assert not is_model_file("")

    def test_none_input(self):
        with pytest.raises(TypeError):
            is_model_file(None)

    @pytest.mark.parametrize("filename, expected", [
        ("/home/user/MODEL.PT", True),
        ("/home/user/Model.Safetensors", True),
        ("/home/user/PYTORCH_MODEL.BIN", True),
        ("/home/user/model_QUANT.bin", True),
    ])
    def test_case_insensitivity(self, filename, expected):
        assert is_model_file(filename) == expected

    @pytest.mark.parametrize("filename, expected", [
        ("model.ckpt", True),
        ("model.pt", True),
        ("model.pth", True),
        ("model.safetensors", True),
        ("model.onnx", True),
        ("model.h5", True),
        ("model.tflite", True),
        ("model.pkl", True),
        ("model.bin", True),
        ("model.params", True),
        ("model.pdparams", True),
        ("model.keras", True),
        ("model.weights", True),
        ("model.pmml", True),
        ("data.txt", False),
        ("image.jpg", False),
        ("archive.zip", False),
    ])
    def test_common_extensions(self, filename, expected):
        assert is_model_file(filename) == expected

    @pytest.mark.parametrize("filename, expected", [
        ("model-00001-of-00002", True),
        ("model.bin.1", True),
        ("model.part.0", True),
        ("model_part_0", True),
        ("model-shard1", True),
        ("model_01", False),
        ("model-part", False),
    ])
    def test_shard_patterns(self, filename, expected):
        assert is_model_file(filename) == expected

    @pytest.mark.parametrize("filename, expected", [
        ("pytorch_model.bin", True),
        ("tf_model.h5", True),
        ("model.ckpt", True),
        ("flax_model.msgpack", True),
        ("model.safetensors", True),
    ])
    def test_huggingface_patterns(self, filename, expected):
        assert is_model_file(filename) == expected

    @pytest.mark.parametrize("filename, expected", [
        ("/home/user/model.pt", True),
        ("C:\\Users\\User\\model.ckpt", True),
        ("/Users/user/Documents/model.safetensors", True),
        ("\\\\server\\share\\model.onnx", True),
    ])
    def test_different_os_paths(self, filename, expected):
        assert is_model_file(filename) == expected

    @pytest.mark.parametrize("filename, expected", [
        ("模型.pt", True),
        ("モデル.ckpt", True),
        ("модель.safetensors", True),
        ("mødel.onnx", True),
    ])
    def test_non_ascii_filenames(self, filename, expected):
        assert is_model_file(filename) == expected

    @pytest.mark.parametrize("filename, expected", [
        ("MODEL.PT", True),
        ("Model.Safetensors", True),
        ("PYTORCH_MODEL.BIN", True),
        ("model_QUANT.bin", True),
    ])
    def test_case_insensitivity(self, filename, expected):
        assert is_model_file(filename) == expected

    @pytest.mark.parametrize("filename, expected", [
        ("model.tar.gz", False),
        ("model.zip", False),
        ("model.npy", False),
        ("model.npz", False),
        ("model.json", False),
        ("model.yaml", False),
        ("model.xml", False),
    ])
    def test_non_model_files(self, filename, expected):
        assert is_model_file(filename) == expected

    @pytest.mark.parametrize("filename, expected", [
        ("model.ckpt.1", True),
        ("model-00001.safetensors", True),
        ("pytorch_model-00001-of-00002.bin", True),
        ("model.ckpt.data-00000-of-00001", True),
    ])
    def test_complex_model_filenames(self, filename, expected):
        assert is_model_file(filename) == expected

    @pytest.mark.parametrize("filename, expected", [
        ("model.engine", True),
        ("model.plan", True),
        ("model.trt", True),
        ("model.torchscript", True),
        ("model.pdiparams", True),
        ("model.pdopt", True),
        ("model.nb", True),
        ("model.mnn", True),
        ("model.ncnn", True),
        ("model.om", True),
        ("model.rknn", True),
        ("model.xmodel", True),
        ("model.kmodel", True),
    ])
    def test_additional_model_formats(self, filename, expected):
        assert is_model_file(filename) == expected

    @pytest.mark.parametrize("filename, expected", [
        ("model-q4_0.gguf", True),
        ("model.q5_1-00001-of-00002", True),
        ("pytorch_model-q8_0.bin", True),
        ("model.ckpt.int8.data-00000-of-00001", True),
    ])
    def test_complex_quantized_filenames(self, filename, expected):
        assert is_model_file(filename) == expected
